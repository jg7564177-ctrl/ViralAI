# ViralAI Android WebView

Ce projet est un wrapper Android léger pour ouvrir l’URL publique HTTPS de ViralAI dans un WebView.

## Objectif

- ouvrir l’application web de ViralAI sur mobile
- conserver l’IA, le chat, les comptes et les crédits côté serveur
- ne pas embarquer de modèles IA lourds dans l’APK
- rester compatible avec le PWA existant

## Paramètres

- application name : ViralAI
- package name : com.viralai.app
- orientation : portrait
- permissions minimales : INTERNET
- HTTPS uniquement : oui
- icône : à fournir dans `res/mipmap`
- splash screen : simple écran de démarrage

## Remplacer l’URL publique

Dans le code du WebView, remplacer :

```java
private static final String APP_URL = "https://example.com";
```

par l’URL réelle de votre déploiement Render ou hébergeur compatible.

## Exemple de commande Gradle

```bash
./gradlew assembleRelease
```

## Vérification minimale

- HTTPS actif
- `manifest.webmanifest` accessible
- `service-worker.js` accessible
- installation PWA possible depuis le site distant
- aucune clé secrète dans l’APK
