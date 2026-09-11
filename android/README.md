# ViralAI Android packaging

Le projet est actuellement un backend Flask + front web. Pour produire une APK Android, il faut utiliser un wrapper mobile léger qui charge l’URL publique de ViralAI, sans embarquer de modèles IA lourds.

## Recommandation

- utiliser un WebView Android léger
- garder le backend sur le serveur
- ne pas embarquer des bibliothèques lourdes dans l’APK
- utiliser HTTPS avec certificat valide
- demander les permissions minimales : internet seulement

## Paramètres de base

- nom : ViralAI
- package : com.viralai.app
- orientation : portrait
- splash screen : écran de démarrage simple avec logo
- icon : logo appli léger
- navigation : adaptative mobile

## Commande exacte pour préparer l’environnement

```bash
mkdir -p android-app
cd android-app
# générer un projet Android WebView ou builder externe selon votre pipeline
```

## Vérification minimale

- URL publique HTTPS accessible
- PWA installable
- navigation web mobile stable
- permissions minimales
- aucun secret stocké dans l’APK
