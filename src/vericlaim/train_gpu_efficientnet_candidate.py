"""CUDA training candidate: fine-tuned EfficientNetV2-S with grouped folds.

It is deliberately a separate candidate, trained only on supplied claim
images.  The candidate never replaces the deployed artifact by itself.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

from .features import extract_features
from .train import choose_classification_threshold, discover, metrics
from .validation import build_perceptual_groups


def focal_loss(logits, labels, class_weights, gamma: float):
    import torch
    probabilities = torch.sigmoid(logits)
    pt = torch.where(labels > 0.5, probabilities, 1 - probabilities).clamp(1e-6, 1 - 1e-6)
    alpha = torch.where(labels > 0.5, class_weights[1], class_weights[0])
    return (-alpha * (1 - pt).pow(gamma) * pt.log()).mean()


def effective_weights(labels: np.ndarray, beta: float, device):
    import torch
    counts = np.asarray([np.sum(labels == 0), np.sum(labels == 1)], dtype=float)
    raw = (1 - beta) / np.clip(1 - np.power(beta, counts), 1e-12, None)
    raw = raw / raw.sum() * 2
    return torch.tensor(raw, dtype=torch.float32, device=device)


def make_loader(paths, labels, training: bool, batch_size: int, workers: int):
    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        *( [transforms.RandomHorizontalFlip(), transforms.RandomRotation(10), transforms.ColorJitter(0.12, 0.12, 0.08), transforms.RandomAffine(0, translate=(0.04, 0.04))] if training else [] ),
        transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    class Claims(Dataset):
        def __len__(self): return len(paths)
        def __getitem__(self, index):
            with Image.open(paths[index]) as image:
                return transform(image.convert("RGB")), torch.tensor(float(labels[index]))
    return DataLoader(Claims(), batch_size=batch_size, shuffle=training, num_workers=workers, pin_memory=True, persistent_workers=workers > 0)


def make_model(device, fine_tune_blocks: int):
    import torch.nn as nn
    from torchvision.models import EfficientNet_V2_S_Weights, efficientnet_v2_s
    model = efficientnet_v2_s(weights=EfficientNet_V2_S_Weights.IMAGENET1K_V1)
    # Only the final visual blocks and classifier adapt to this small dataset.
    for parameter in model.features.parameters(): parameter.requires_grad = False
    for block in list(model.features.children())[-fine_tune_blocks:]:
        for parameter in block.parameters(): parameter.requires_grad = True
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(nn.Dropout(0.35), nn.Linear(in_features, 1))
    return model.to(device)


def predict(model, loader, device):
    import torch
    model.eval(); output = []
    with torch.no_grad():
        for images, _ in loader:
            output.extend(torch.sigmoid(model(images.to(device, non_blocking=True))).flatten().cpu().numpy())
    return np.asarray(output, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/gpu_efficientnet_candidate"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--patience", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    # Windows uses spawn; keeping this at zero avoids pickling the local
    # dataset wrapper while CUDA still performs all model computation.
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--fine-tune-blocks", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--beta", type=float, default=0.9999)
    parser.add_argument("--gamma", type=float, default=2.0)
    parser.add_argument("--perceptual-distance", type=int, default=6)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    import torch
    if not torch.cuda.is_available(): raise SystemExit("CUDA GPU not available to PyTorch")
    torch.manual_seed(42); np.random.seed(42); device = torch.device("cuda")
    train_paths, y_train = discover(args.data_root, "train"); test_paths, y_test = discover(args.data_root, "test")
    # Reuse the existing deterministic feature audit when available. This
    # avoids spending GPU-training time recomputing identical fingerprints.
    feature_cache = args.cache_dir / "train_features.joblib"
    cached = joblib.load(feature_cache) if feature_cache.exists() else None
    if cached and cached.get("paths") == [str(path) for path in train_paths]:
        hashes = [row["perceptual_hash"] for row in cached["forensics"]]
    else:
        hashes = [extract_features(path)[1].perceptual_hash for path in train_paths]
    groups = build_perceptual_groups(hashes, args.perceptual_distance)
    folds = list(StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=42).split(train_paths, y_train, groups))
    oof = np.zeros(len(y_train), dtype=np.float32); test = np.zeros(len(y_test), dtype=np.float32); saved = []; started = time.time()
    for fold, (fit, validation) in enumerate(folds, 1):
        model = make_model(device, args.fine_tune_blocks); optimiser = torch.optim.AdamW(filter(lambda p:p.requires_grad, model.parameters()), lr=args.learning_rate, weight_decay=1e-4)
        weights = effective_weights(y_train[fit], args.beta, device); scaler = torch.amp.GradScaler("cuda"); best, best_auc, stale = None, -1., 0
        train_loader = make_loader([train_paths[i] for i in fit], y_train[fit], True, args.batch_size, args.workers)
        validation_loader = make_loader([train_paths[i] for i in validation], y_train[validation], False, args.batch_size, args.workers)
        for epoch in range(args.epochs):
            model.train()
            for images, labels in train_loader:
                optimiser.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.float16): loss = focal_loss(model(images.to(device, non_blocking=True)).flatten(), labels.to(device, non_blocking=True), weights, args.gamma)
                scaler.scale(loss).backward(); scaler.step(optimiser); scaler.update()
            validation_scores = predict(model, validation_loader, device)
            # Average precision is the right early-stop signal for rare fraud.
            from sklearn.metrics import average_precision_score
            score = average_precision_score(y_train[validation], validation_scores)
            if score > best_auc:
                best_auc, stale = score, 0; best = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
            else:
                stale += 1
                if stale >= args.patience: break
        model.load_state_dict(best); checkpoint = args.output_dir / f"fold_{fold}.pt"; torch.save(model.state_dict(), checkpoint)
        oof[validation] = predict(model, validation_loader, device)
        test += predict(model, make_loader(test_paths, y_test, False, args.batch_size, args.workers), device) / args.folds
        saved.append({"fold":fold,"model":checkpoint.name,"validation_pr_auc":round(float(best_auc),4),"fit_images":len(fit),"validation_images":len(validation)})
        del model; torch.cuda.empty_cache()
    calibrator = LogisticRegression(C=1000, max_iter=2000, random_state=42).fit(oof.reshape(-1,1), y_train)
    calibrated_oof = calibrator.predict_proba(oof.reshape(-1,1))[:,1]; calibrated_test = calibrator.predict_proba(test.reshape(-1,1))[:,1]
    threshold = choose_classification_threshold(y_train, calibrated_oof)
    report = {"project":"VeriClaim AI","candidate":True,"model":"CUDA fine-tuned EfficientNetV2-S + class-balanced focal loss","device":torch.cuda.get_device_name(0),"dataset_policy":"Supplied claim images only; no external claim images or synthetic claim data.","training":{"augmentation":["horizontal flip","small rotation","colour jitter","small translation"],"loss":"class-balanced focal","beta":args.beta,"gamma":args.gamma,"fine_tune_blocks":args.fine_tune_blocks,"folds":args.folds},"validation":{"method":"StratifiedGroupKFold on perceptual image clusters","groups":int(len(np.unique(groups)))},"folds":saved,"classification_threshold":float(threshold),"oof_metrics":metrics(y_train,calibrated_oof,threshold),"test_metrics":metrics(y_test,calibrated_test,threshold),"elapsed_seconds":round(time.time()-started,1)}
    (args.output_dir / "candidate_metrics.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2))

if __name__ == "__main__": main()
