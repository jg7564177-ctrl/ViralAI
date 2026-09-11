# Google Play release checklist – ViralAI

## 1. Préparer un compte développeur

- Créer un compte Google Play Developer
- Payer le droit d’inscription Google Play
- Vérifier les règles valides sur le compte et le profil développeur

## 2. Préparer le build Android

- Utiliser le projet prêt à compiler dans `android-app/`
- Remplacer l’URL publique HTTPS dans le code du WebView
- Vérifier que le site distant est accessible en HTTPS
- Vérifier que le manifest PWA et le service worker sont bien servis depuis le site public

## 3. Générer le bundle signée

```bash
./gradlew bundleRelease
```

Ou, si le SDK Android est installé localement :

```bash
./gradlew assembleRelease
```

## 4. Signer l’application

- Générer un keystore Android de type `upload` ou `release`
- Enregistrer le fichier keystore
- Préparer `key.properties` avec `storeFile`, `storePassword`, `keyAlias`, `keyPassword`
- Vérifier la signature avant l’envoi

## 5. Remplir la fiche Play Store

- Nom : ViralAI
- Catégorie : Outils / Productivité / Média
- Description courte : à remplir
- Description longue : voir `release/LONG_DESCRIPTION.md`
- Icône : fournir l’icône de l’application
- Captures d’écran : télécharger dans `release/screenshots/`
- Politique de confidentialité : à créer séparément
- Déclaration de confidentialité : à renseigner dans le compte Play
- URL du site public : à renseigner si disponible

## 6. Soumettre le bundle

- Charger le fichier `.aab` généré
- Vérifier la qualité de la fiche
- Soumettre pour revue Google Play
- Attendre validation

## 7. Points de vigilance

- L’APK ne doit pas embarquer de modèle IA lourd
- Le backend reste responsable de l’IA et des crédits
- L’URL publique doit être HTTPS uniquement
- Les paiements doivent rester désactivés jusqu’à activation explicite d’un fournisseur réel

## 8. Package / version

- package name : `com.viralai.app`
- version : `1.0.0`
- version code : `1`
