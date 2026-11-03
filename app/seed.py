from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models.enums import RoleUtilisateur
from app.models.type_vetement import TypeVetement
from app.models.utilisateur import Utilisateur
from app.security import hash_password

# Annexe B : (nom, description, prix_base FCFA, delai_jours)
CATALOGUE = [
    ("Boubou", "Boubou homme en bazin ou brodé", 35000, 10),
    ("Costume 2 pièces", "Veste et pantalon", 85000, 14),
    ("Robe", "Robe sur mesure", 30000, 7),
    ("Ensemble wax", "Tenue deux pièces en wax", 25000, 7),
    ("Chemise", "Chemise sur mesure", 15000, 5),
    ("Pantalon", "Pantalon sur mesure", 12000, 4),
    ("Retouche", "Ourlet, rétrécissement, remplacement de fermeture", 3000, 2),
]


def creer_admin(db) -> None:
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        raise SystemExit("ADMIN_EMAIL et ADMIN_PASSWORD doivent être définis dans le .env")

    email = settings.ADMIN_EMAIL.lower()
    existant = db.scalar(select(Utilisateur).where(Utilisateur.email == email))
    if existant:
        print(f"Admin déjà présent : {email}")
        return

    db.add(
        Utilisateur(
            email=email,
            nom_complet=settings.ADMIN_NOM_COMPLET,
            mot_de_passe_hash=hash_password(settings.ADMIN_PASSWORD),
            role=RoleUtilisateur.admin,
            actif=True,
        )
    )
    print(f"Admin créé : {email}")


def creer_catalogue(db) -> None:
    for nom, description, prix, delai in CATALOGUE:
        # Idempotent : on ne recrée pas une prestation qui existe déjà
        if db.scalar(select(TypeVetement).where(TypeVetement.nom == nom)):
            continue
        db.add(
            TypeVetement(
                nom=nom, description=description,
                prix_base=prix, delai_jours=delai, actif=True,
            )
        )
        print(f"Prestation créée : {nom}")


def main() -> None:
    with SessionLocal() as db:
        creer_admin(db)
        creer_catalogue(db)
        db.commit()  # une seule transaction pour tout le seed


if __name__ == "__main__":
    main()