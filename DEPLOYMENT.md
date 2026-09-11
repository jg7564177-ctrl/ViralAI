# Déploiement ViralAI

## Solution choisie : Render Web Service

ViralAI est une application Flask Python compatible avec une plateforme web HTTP de type Render. Cette solution est adaptée au projet actuel car :

- le backend est Flask/Python
- le projet contient `app.py`, `requirements.txt`, templates et static
- le service fournit HTTPS public
- le projet peut être mis derrière un domaine ou une URL publique
- la configuration de sécurité reste serveur-only

Important : aucune URL publique n’a été créée dans cet environnement car aucun compte Render/Railway ni identifiants de publication ne sont disponibles ici.

## Fichiers de déploiement préparés

Le dépôt contient désormais :

- `render.yaml`
- `Procfile`
- `runtime.txt`
- `requirements.txt` avec `gunicorn`

## Étapes exactes pour publier sur Render

1. Ouvrir https://dashboard.render.com
2. Cliquer sur `New` puis `Web Service`
3. Choisir `Build and deploy from a Git repository`
4. Connecter votre dépôt GitHub contenant ViralAI
5. Sélectionner la branche `main`
6. Configurer :
   - Name : `viralai`
   - Region : la plus proche de votre audience
   - Runtime : `Python`
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `gunicorn app:app --bind 0.0.0.0:$PORT`
7. Ajouter les variables d’environnement suivantes :

```env
SECRET_KEY=remplacer-par-une-cle-secrete-forte
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

8. Cliquer sur `Create Web Service`
9. Attendre le premier build puis vérifier l’URL publique fournie par Render.

## Vérification HTTPS et PWA

Une fois l’URL publique disponible, vérifier exactement :

```bash
curl -I https://<votre-url>/health
curl -I https://<votre-url>/landing
curl -I https://<votre-url>/manifest.webmanifest
curl -I https://<votre-url>/service-worker.js
```

Contrôles requis :

- le site est servi avec HTTPS
- `/landing` répond bien
- `/manifest.webmanifest` est accessible
- `/service-worker.js` est accessible
- l’API fonctionne via HTTPS
- les routes de paiement restent désactivées par défaut
- `ALLOW_PAID_VIDEO=false` reste strictement respecté

## Vérification fonctionnelle minimale

- `/` -> page principale de l’application
- `/landing` -> landing publique
- `/health` -> OK
- `/api/payments/checkout` -> retourne `PAYMENT_NOT_CONFIGURED`
- `/api/video/jobs` -> ne lance aucune génération vidéo réelle si le fournisseur est désactivé
- /manifest + PWA sur Android -> installation possible via HTTPS

## Sécurité conservée

Aucune modification n’a été faite pour casser le système de sécurité existant :

- aucun paiement réel activé
- aucun fournisseur vidéo activé
- aucun crédit accordé côté navigateur
- aucune clé secrète exposée dans le frontend

## Android / APK

Une APK native n’a pas été compilée dans ce conteneur, car il n’y a ni SDK Android ni compte de publication disponible ici. Le projet Android WebView léger est préparé dans le dossier `android-app/` avec une URL publique modifiable à remplacer dans les fichiers de configuration.

## À faire chez toi pour terminer la publication

1. Créer le compte Render ou un autre hébergeur compatible
2. Pousser le dépôt GitHub
3. Déployer le service
4. Récupérer l’URL publique HTTPS
5. Remplacer l’URL publique dans le projet Android WebView
6. Compiler l’APK dans un environnement Android complet
7. Publier vers Google Play uniquement avec un compte développeur valide

Ne pas publier d’APK ou d’URL si ces étapes n’ont pas été exécutées réellement.
