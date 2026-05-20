from app.models.connected_app import ConnectedApp


def compute_commission_and_net(app: ConnectedApp, amount: float, provider_fees: float = 0.0) -> tuple[float, float]:
    commission = 0.0
    if app.commission_type == "fixed":
        commission = app.commission_value
    elif app.commission_type == "percentage":
        commission = (app.commission_value / 100.0) * amount
    net_amount = amount - provider_fees - commission
    return round(max(commission, 0.0), 2), round(max(net_amount, 0.0), 2)
