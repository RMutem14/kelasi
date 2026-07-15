# Huduma

Plateforme collaborative de gestion pédagogique et de commercialisation
des contenus éducatifs destinée au **Collège Saint Joseph/Elikya**.

## Stack technique

- **Backend** : Django 5.1 LTS, PostgreSQL (SQLite en dev)
- **Frontend** : Django Templates + HTMX + Alpine.js + TailwindCSS
- **Auth** : Sessions Django, modèle User personnalisé (email + UUID + rôles)

## Démarrage rapide

```bash
# 1. Cloner le dépôt et se placer dans le dossier
cd huduma

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements/dev.txt

# 4. Copier et adapter le fichier .env
cp .env.example .env
# Éditer .env pour ajuster SECRET_KEY et la DB si besoin

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer les utilisateurs de test (admin, enseignant, directeur, élève)
python manage.py seed_users

# 7. Lancer le serveur de développement
python manage.py runserver
```

Accéder à http://127.0.0.1:8000/

## Comptes de test

Tous les comptes ont le mot de passe : `Huduma2026!`

| Email                  | Rôle                | Accès admin Django |
| ---------------------- | ------------------- | ------------------ |
| `admin@elikya.cd`      | Administrateur      | ✓ (superuser)      |
| `enseignant@elikya.cd` | Enseignant          | ✗                  |
| `directeur@elikya.cd`  | Directeur des études| ✗                  |
| `eleve@elikya.cd`      | Élève               | ✗                  |

## Architecture du projet

```
huduma/
├── config/                  # Configuration Django
│   ├── settings/            # Settings split (base / dev / prod)
│   ├── urls.py              # URLs racine
│   ├── asgi.py / wsgi.py
│   └── __init__.py
│
├── apps/                    # Applications Django modulaires
│   ├── accounts/            # Utilisateurs + authentification
│   ├── core/                # Fondations techniques (BaseModel, managers, constants, mixins, permissions, utils)
│   ├── dashboard/           # Tableaux de bord par rôle
│   ├── academic/            # (Sprint 1) Classes, matières, années
│   ├── pedagogy/            # (Sprint 2-3) Documents pédagogiques
│   ├── validation/          # (Sprint 4) Workflow validation
│   ├── marketplace/         # (Sprint 5) Catalogue, achats, téléchargements
│   ├── students/            # (Sprint 6) Notes, ressources élèves
│   └── notifications/       # Notifications internes
│
├── templates/               # Templates Django
│   ├── layouts/             # base.html, auth.html, dashboard.html
│   ├── components/          # Composants réutilisables
│   │   ├── forms/           # input, textarea, select, checkbox, radio
│   │   ├── navigation/      # breadcrumb, dropdown, pagination
│   │   ├── tables/          # table (HTMX-ready)
│   │   ├── feedback/        # alert, status_badge, spinner, empty_state
│   │   ├── cards/           # card, stats_card
│   │   └── modals/          # modal (HTMX + Alpine.js)
│   ├── partials/            # sidebar, navbar, footer, messages
│   ├── pages/               # Pages organisées par module
│   │   ├── dashboard/       # admin, enseignant, directeur, eleve
│   │   └── accounts/        # login
│   └── errors/              # 403, 404, 500
│
├── static/                  # Fichiers statiques (CSS, JS, images)
├── media/                   # Uploads utilisateurs
├── requirements/            # Dépendances Python (base / dev / prod)
├── manage.py
├── pyproject.toml
└── .env.example
```

## Modèle de données de base

### User (apps.accounts)

- UUID (hérité de `BaseModel`)
- `email` (identifiant principal, unique)
- `first_name`, `last_name`
- `role` (parmi ADMIN, ENSEIGNANT, DIRECTEUR_ETUDES, ELEVE)
- `phone`, `avatar` (optionnels)
- `is_active`, `is_staff`, `is_superuser`
- Horodatage + audit (created_by, updated_by) + soft delete (deleted_at)

Propriétés pratiques : `is_admin`, `is_teacher`, `is_director`, `is_student`,
`full_name`, `short_label`, `initials`.

### BaseModel (apps.core.models.base)

Tous les modèles métier héritent de `BaseModel` qui combine :
- `TimeStampedModel` (created_at, updated_at)
- `UUIDModel` (id UUID)
- `AuditModel` (created_by, updated_by)
- `SoftDeleteModel` (deleted_at + ActiveManager / AllObjectsManager)

## Constantes globales

Centralisées dans `apps/core/constants.py` :
- `DocumentStatus` : BROUILLON, SOUMIS, CORRECTION, VALIDE, REJETE
- `PublicationStatus` : BROUILLON, PUBLIE, ARCHIVE, RETIRE
- `OrderStatus` : EN_ATTENTE, PAYE, ECHOUE, REMBOURSE
- `ResourceType` : SYLLABUS, SUPPORT, EXERCICE, TP, EXAMEN, LIVRE, CORRIGE
- `ResourceCategory` : COURS, EXERCICE, EVALUATION, REFERENCE, METHODOLOGIE
- `NotificationLevel` : INFO, SUCCESS, WARNING, ERROR

## Sprint 0 — État

Cette itération pose les fondations techniques. Aucune logique métier.

### Validé

- [x] Architecture modulaire 10 apps
- [x] Settings split base/dev/prod
- [x] Modèle User personnalisé (email + UUID + 4 rôles)
- [x] BaseModel abstrait (UUID + TimeStamped + Audit + SoftDelete)
- [x] Managers ActiveManager / AllObjectsManager
- [x] Constantes globales centralisées
- [x] Mixins (RoleRequiredMixin, HTMXMixin)
- [x] Permissions par rôle
- [x] Auth Login / Logout
- [x] Dashboard par rôle (admin, enseignant, directeur, élève)
- [x] Sidebar dynamique par rôle
- [x] Navbar avec menu utilisateur
- [x] Handlers 403 / 404 / 500
- [x] Page design-system (palette + statuts + rôles)
- [x] seed_users management command
- [x] Tests E2E passants

### À faire (Phase 2 — après réception templates client)

- [ ] Design system complet (17 composants)
- [ ] TailwindCSS build local (sans CDN)
- [ ] HTMX + Alpine.js en local (sans CDN)
- [ ] Dashboards par rôle avec mise en page définitive

## Commandes utiles

```bash
# Lancer les tests
python manage.py test

# Créer un superuser interactif
python manage.py createsuperuser

# Créer les utilisateurs de test
python manage.py seed_users

# Collecter les statiques (production)
python manage.py collectstatic

# Shell Django
python manage.py shell
```

## Conventions de code

- PEP 8 strict
- Variables et fonctions explicites
- Docstrings en français pour les classes, modèles, managers et fonctions publiques
- Commentaires en français lorsqu'ils apportent une réelle valeur
- Pas de logique métier dans les templates (utiliser des template tags/filters)

## Licence

Projet privé — Collège Saint Joseph/Elikya. Tous droits réservés.
