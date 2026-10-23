"""Documented model-sensitivity fallback; no model mutation or SHAP dependency."""


def top_drivers(model, frame, reference, prediction):
    items = []
    for name in frame.columns:
        if name not in reference:
            continue
        changed = frame.copy()
        changed[name] = reference[name]
        delta = prediction - float(model.predict(changed)[0])
        items.append({"feature": name, "difference": delta})
    return sorted(items, key=lambda item: abs(item["difference"]), reverse=True)[:3]
