# Dossier technique SerdiPay / Railway

## Situation active chez SerdiPay

- Merchant Code : `513237`
- Domaine web : `https://pay.badiboss.com`
- Callback : `https://pay.badiboss.com/serdipay/callback`
- IP whitelistée : `66.33.22.87`
- Statut : actif

## Preuves réseau

### DNS public

`pay.badiboss.com` pointe vers Railway :

```text
pay.badiboss.com CNAME uq06mq8.up.railway.app
uq06mq8.up.railway.app A 66.33.22.87
```

### Nature de `66.33.22.87`

`66.33.22.87` est une IP d'entrée Railway :

- HTTP direct retourne l'en-tête `Server: railway-edge`
- RDAP ARIN : réseau `RLWY-EDGE-01`, organisation Railway
- Ports proxy testés :
  - `3128` : fermé
  - `8080` : fermé

Conclusion : `66.33.22.87` est une IP d'entrée/load balancer Railway. Elle ne fournit pas de proxy HTTP(S) exploitable pour les appels sortants.

## Diagnostic production Badiboss Pay

Endpoint :

```text
GET https://pay.badiboss.com/payments/serdipay/egress
```

Résultat observé :

```json
{
  "public_domain": "pay.badiboss.com",
  "callback_url": "https://pay.badiboss.com/serdipay/callback",
  "public_domain_dns": {
    "domain": "pay.badiboss.com",
    "addresses": ["66.33.22.87"],
    "error": null
  },
  "proxy_configured": false,
  "expected_outbound_ip": "66.33.22.87",
  "railway_direct_egress": {
    "status_code": 200,
    "observed_outbound_ip": "162.220.234.15",
    "matches_expected_ip": false,
    "error": null
  },
  "serdipay_token_direct": {
    "status_code": 400,
    "token_present": false,
    "response_keys": ["message"],
    "message": "This domain or IP is not whitelisted ",
    "error": null
  },
  "conclusion": "L'IP attendue correspond au domaine public/edge Railway, mais pas a l'IP sortante du service. Elle ne peut pas etre utilisee comme egress sans passerelle controlee."
}
```

## Résultat SerdiPay

Endpoint testé :

```text
POST https://pay.badiboss.com/api/test-token
```

Résultat :

```text
status_code=400
response_keys=message
token_present=false
message=This domain or IP is not whitelisted
```

## Conclusion technique

SerdiPay a whitelisté l'IP d'entrée Railway (`66.33.22.87`), mais les appels API SerdiPay sont filtrés sur l'IP source sortante du conteneur Railway.

Flux entrants :

```text
SerdiPay/client -> pay.badiboss.com -> Railway edge 66.33.22.87 -> Badiboss Pay
```

Flux sortants actuels :

```text
Badiboss Pay Railway container -> Internet -> SerdiPay
IP source observée : 162.220.234.15
```

Ces deux IP ne sont pas les mêmes.

## Demande à Railway

Nous devons éviter un nouveau changement administratif chez SerdiPay. Merci de fournir l'une des options suivantes :

1. Faire sortir le service Railway Badiboss Pay vers Internet avec l'IP source exacte `66.33.22.87`.
2. Fournir une passerelle egress/proxy Railway contrôlée dont l'IP source vers Internet est `66.33.22.87`.
3. Confirmer officiellement que `66.33.22.87` est uniquement une IP d'entrée edge et ne peut pas être utilisée en egress, puis fournir l'IP static outbound exacte à faire valider par SerdiPay.

## Demande à SerdiPay si Railway confirme l'impossibilité

Le domaine et callback sont corrects et fonctionnels :

```text
https://pay.badiboss.com
https://pay.badiboss.com/serdipay/callback
```

La whitelist doit porter sur l'IP source sortante réelle des appels API, actuellement :

```text
162.220.234.15
```

ou sur une IP static outbound fournie officiellement par Railway après activation.

## État applicatif

Badiboss Pay est prêt côté code :

- Le connecteur SerdiPay peut utiliser `SERDIPAY_OUTBOUND_PROXY_URL` si une passerelle réelle existe.
- Le diagnostic `/payments/serdipay/egress` vérifie l'IP observée et le test token SerdiPay sans exposer les credentials.
- Le domaine, callback, dashboard, auth JWT, routes admin et frontend restent inchangés.
