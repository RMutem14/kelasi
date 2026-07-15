# Huduma|Kelasi — Installation & Démarrage

Ce guide vous permet de lancer le projet Huduma en quelques minutes sur votre machine.

---

## Prérequis

| Outil | Version requise | Vérification |
|-------|----------------|--------------|
| **Python** | 3.12+ | `python3 --version` |
| **pip** | 23+ | `pip3 --version` |
| **Git** | 2.30+ | `git --version` |

> **PostgreSQL** est optionnel en dev (SQLite est utilisé par défaut).
> Il ne sera nécessaire qu'en production.

---

## Installation en 4 étapes

### 1. Extraire le projet

```bash
# Extraire l'archive où vous le souhaitez
unzip huduma.zip
cd huduma
```

### 2. Créer un environnement virtuel (recommandé)

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```bash
pip install -r requirements/dev.txt
```

> Cela installe Django 5.1, python-dotenv, psycopg2-binary et django-debug-toolbar.

### 4. Lancer le serveur

```bash
python manage.py runserver
```

**C'est prêt !** Ouvrez http://127.0.0.1:8000/ dans votre navigateur.

---

## Comptes de test

La base de données SQLite est **pré-remplie** avec 4 utilisateurs. Vous pouvez vous connecter immédiatement.

**Mot de passe pour tous les comptes : `Huduma2026!`**

| Email | Rôle | Description |
|-------|------|-------------|
| `admin@elikya.cd` | Administrateur | Accès complet + admin Django |
| `enseignant@elikya.cd` | Enseignant | Travail pédagogique + boutique |
| `directeur@elikya.cd` | Directeur des études | Validation des documents |
| `eleve@elikya.cd` | Élève | Consultation + achat + notes |

---

## Que tester ?

### Authentification
1. Allez sur http://127.0.0.1:8000/
2. Vous êtes redirigé vers la page de connexion
3. Connectez-vous avec chaque compte pour voir le dashboard correspondant

### Dashboards par rôle
- **Admin** : stats + table comptes récents + actions rapides
- **Enseignant** : 2 espaces (pédagogique + boutique)
- **Directeur** : file de validation + consultation classes/cours
- **Élève** : ressources + catalogue + notes

### Design System
- Allez sur http://127.0.0.1:8000/design-system/
- Visualisez les 15 composants réutilisables

### Admin Django
- Allez sur http://127.0.0.1:8000/admin/
- Connectez-vous avec `admin@elikya.cd`
- Gérez les utilisateurs depuis l'interface admin

### Pages d'erreur
- http://127.0.0.1:8000/page-inexistante/ → page 404 personnalisée
- Déconnexion → redirection automatique vers login

### Responsive
- Réduisez la fenêtre du navigateur sous 1280px de large
- La sidebar devient un menu coulissant (bouton burger en haut à gauche)

---

## Réinitialiser la base de données

Si vous voulez repartir de zéro :

```bash
# Supprimer la base SQLite
rm db.sqlite3

# Recréer les migrations et la base
python manage.py migrate

# Recréer les 4 utilisateurs de test
python manage.py seed_users
```

---

## Dépannage

### Erreur `ModuleNotFoundError: No module named 'django'`
→ L'environnement virtuel n'est pas activé. Exécutez `source .venv/bin/activate`.

### Erreur `Port 8000 already in use`
→ Utilisez un autre port : `python manage.py runserver 8080`

### Les icônes Lucide ne s'affichent pas
→ Vérifiez votre connexion internet (les icônes sont chargées via CDN).
En production, il faudra les télécharger localement dans `static/vendor/`.

### La page de login s'affiche sans style CSS
→ Vérifiez que TailwindCSS est accessible (chargé via CDN, nécessite internet).

---

## Structure du projet

```
huduma/
├── apps/                    # Applications Django
│   ├── accounts/            # Utilisateurs + auth
│   ├── core/                # Fondations (BaseModel, managers, constants)
│   ├── dashboard/           # Tableaux de bord par rôle
│   ├── academic/            # (Sprint 1) Classes, matières
│   ├── pedagogy/            # (Sprint 2-3) Documents pédagogiques
│   ├── validation/          # (Sprint 4) Workflow validation
│   ├── marketplace/         # (Sprint 5) Catalogue, achats
│   ├── students/            # (Sprint 6) Notes, ressources
│   └── notifications/       # Notifications internes
├── config/                  # Settings Django
│   └── settings/            # base.py / dev.py / prod.py
├── templates/               # Templates HTML
│   ├── layouts/             # base, auth, dashboard
│   ├── components/          # 15 composants réutilisables
│   ├── partials/            # sidebar, navbar, footer
│   ├── pages/               # Pages par module
│   └── errors/              # 403, 404, 500
├── static/                  # CSS, JS, images
├── media/                   # Uploads utilisateurs
├── requirements/            # Dépendances Python
├── manage.py
├── pyproject.toml
├── .env                     # Configuration (pré-rempli pour dev)
├── .env.example             # Template de configuration
├── db.sqlite3               # Base SQLite avec 4 users de test
└── README.md                # Documentation complète
```

---

## Documentation complémentaire

- **README.md** — Documentation technique complète du projet
- **Documentation tutoriel** (.docx / .pptx / .pdf) — Guide visuel avec captures d'écran

---

## Support

Pour toute question ou problème :
- Consultez le fichier `README.md` à la racine du projet
- Vérifiez la section Dépannage ci-dessus
- Contactez l'équipe de développement

---

**Huduma|Kelasi — Sprint 0 — Collège Saint Joseph/Elikya**
*Préparé par Z.ai — Juillet 2026*
