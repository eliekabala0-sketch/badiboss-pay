# Sortie SerdiPay via 66.33.22.87

SerdiPay a whitelisté l'adresse sortante `66.33.22.87`. Les appels Badiboss Pay vers SerdiPay doivent donc sortir par une infrastructure qui possède réellement cette IP.

## Conclusion Railway

Railway peut fournir une IP sortante statique à un service, mais cette IP est attribuée par Railway et liée à la région du service. Railway ne permet pas de choisir arbitrairement `66.33.22.87` comme IP sortante.

## Architecture retenue

Badiboss Pay reste hébergé sur Railway avec `https://pay.badiboss.com`.

Seuls les appels sortants SerdiPay sont routés via un proxy HTTP(S) installé sur le serveur/VPS qui possède `66.33.22.87` :

- `get-token`
- `payment-merchant`
- diagnostic d'egress SerdiPay

Les callbacks entrants SerdiPay restent inchangés :

`https://pay.badiboss.com/serdipay/callback`

## Variables Railway à configurer

```text
SERDIPAY_OUTBOUND_PROXY_URL=http://user:password@66.33.22.87:3128
SERDIPAY_EXPECTED_OUTBOUND_IP=66.33.22.87
```

Le proxy doit accepter uniquement le service Badiboss Pay et relayer les requêtes HTTPS vers `serdipay.com`.

## Vérification

Après déploiement, appeler en administrateur :

```text
GET /payments/serdipay/egress
```

Le résultat attendu est :

```json
{
  "proxy_configured": true,
  "expected_outbound_ip": "66.33.22.87",
  "observed_outbound_ip": "66.33.22.87",
  "matches_expected_ip": true
}
```
