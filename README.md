# ViralAI

ViralAI est une application web moderne de création, analyse et préparation de contenus vidéo assistée par IA.

## Fonctionnalités

- interface premium mobile-first
- landing page publique
- chat IA orienté création et brainstorming
- génération de scénarios et plans de scènes
- gestion de projets et conversations
- système de crédits côté serveur
- packs de crédits configurables par admin
- architecture de paiements prête à brancher un fournisseur externe
- PWA installable
- préparation Android/WebView sans embarquer de gros modèles IA

## Démarrage rapide

```bash
python -m pip install -r requirements.txt
python app.py
```

Puis ouvrir : http://localhost:5000

## Variables d’environnement

Créer un fichier `.env` ou configurer les variables côté hébergeur.

```env
SECRET_KEY=change-me
AI_PROVIDER=local
AI_API_KEY=
AI_MODEL=
VIDEO_PROVIDER=disabled
ALLOW_PAID_VIDEO=false
PAYMENT_PROVIDER=not_configured
PAYMENT_PROVIDER_API_KEY=
VIDEO_PROVIDER_API_KEY=
VIDEO_PROVIDER_BASE_URL=
VIDEO_PROVIDER_MODEL=
UPLOAD_FOLDER=./uploads
TIKTOK_CLIENT_ID=
YOUTUBE_CLIENT_ID=
```

### Rôle des variables

- `AI_PROVIDER`: fournisseur IA sélectionné (`local` ou `openai`)
- `AI_API_KEY`: clé externe si un vrai fournisseur IA est activé
- `VIDEO_PROVIDER`: doit rester `disabled` tant qu’aucune génération vidéo payante n’est autorisée
- `ALLOW_PAID_VIDEO`: doit rester `false` par défaut
- `PAYMENT_PROVIDER`: nom du fournisseur de paiement si activé ultérieurement
- `TIKTOK_CLIENT_ID`, `YOUTUBE_CLIENT_ID`: préparation OAuth sécurisée

> Aucune clé ne doit être stockée dans le frontend, le manifest, le JS ou le dépôt public.

## Tests

```bash
python -m pytest -q
```

## IA et vidéo

- Le mode IA local est le fallback sûr.
- Les fournisseurs externes ne sont pas activés tant qu’aucune clé et autorisation n’ont été validées.
- La génération vidéo payante est désactivée par défaut.
- Aucun faux résultat vidéo n’est affiché comme réel.

## Crédits et paiements

- les crédits sont gérés côté serveur
- les packs peuvent être configurés par admin
- le prix promo `-50 %` est calculé côté backend
- les paiements sont préparés sans activer de fournisseur réel
- l’API `/api/payments/checkout` retourne `PAYMENT_NOT_CONFIGURED` tant qu’aucun fournisseur n’est branché
- protection maximale contre les doublons de transaction

## PWA et installation

- le manifest est servi sur `/manifest.webmanifest`
- le service worker est servi sur `/service-worker.js`
- l’application peut être installée depuis un navigateur compatible
- sur HTTPS, l’installation hors localhost est possible

## Android

- ViralAI est préparé comme application web mobile / WebView légère
- aucun modèle IA lourd n’est embarqué dans l’APK
- l’APK native nécessite un wrapper Android séparé et un serveur tiers pour les modèles lourds

Voir aussi : `DEPLOYMENT.md` et `android/README.md`.

## Déploiement

Voir le guide complet dans [DEPLOYMENT.md](DEPLOYMENT.md).

## Sécurité

- authentification par en-tête utilisateur pour le test local
- routes admin protégées côté serveur
- aucun accès intercompte entre comptes
- cartes de crédits et paiements serveur-only
- validation des entrées et pas d’augmentation de crédit depuis le navigateur

## Limites actuelles

- aucun fournisseur de paiement réel n’est activé
- aucun modèle vidéo payant n’est lancé automatiquement
- toute intégration externe nécessite des clés, validation et accord explicite
