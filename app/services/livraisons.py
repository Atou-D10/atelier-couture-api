from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflitError, IntrouvableError, ValidationMetierError
from app.models.client import Client
from app.models.commande import Commande
from app.models.enums import ModeLivraison, StatutCommande, StatutLivraison
from app.models.historique_statut import HistoriqueStatut
from app.models.livraison import Livraison
from app.models.utilisateur import Utilisateur
from app.schemas.livraison import LivraisonConfirmer, LivraisonPlanifier
from app.services.commandes import verifier_modifiable


def _commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise IntrouvableError(f"Commande {commande_id} introuvable.")
    return commande


def planifier(db: Session, commande_id: int, data: LivraisonPlanifier) -> Livraison:
    """Route 35 : crée ou replanifie (une seule livraison par commande)."""
    commande = _commande(db, commande_id)
    verifier_modifiable(commande)  # 409 si livrée ou annulée

    # RG18 : adresse obligatoire à domicile (422)
    if data.mode == ModeLivraison.domicile and not (data.adresse and data.adresse.strip()):
        raise ValidationMetierError("Une livraison à domicile exige une adresse.")

    livraison = commande.livraison
    if livraison is None:
        livraison = Livraison(statut=StatutLivraison.planifiee)
        commande.livraison = livraison
    livraison.mode = data.mode
    livraison.date_prevue = data.date_prevue
    livraison.adresse = data.adresse
    livraison.livreur = data.livreur
    livraison.notes = data.notes

    # RG18 : met à jour la date de livraison prévue de la commande
    commande.date_livraison_prevue = data.date_prevue
    db.flush()
    return livraison


def obtenir(db: Session, commande_id: int) -> Livraison:
    commande = _commande(db, commande_id)
    if commande.livraison is None:
        raise IntrouvableError("Aucune livraison n'est planifiée pour cette commande.")
    return commande.livraison


def confirmer(
    db: Session, commande_id: int, data: LivraisonConfirmer, utilisateur: Utilisateur
) -> Commande:
    """Route 37 : remise du vêtement au client (RG19, RG20)."""
    commande = _commande(db, commande_id)

    # RG19 : la commande doit être « terminee » (409)
    if commande.statut != StatutCommande.terminee:
        raise ConflitError(
            f"Confirmation impossible : la commande est « {commande.statut.value} », "
            "elle doit être « terminee »."
        )

    # RG19 : soldée, sauf autorisation explicite
    impaye = commande.solde > 0
    if impaye and not data.autoriser_solde_impaye:
        raise ConflitError(
            f"Confirmation impossible : il reste {commande.solde} FCFA impayés. "
            "Encaissez le solde ou envoyez autoriser_solde_impaye à vrai."
        )

    date_effective = data.date_effective or date.today()

    # RG20 : livraison retrait_atelier créée automatiquement si absente
    livraison = commande.livraison
    if livraison is None:
        livraison = Livraison(
            mode=ModeLivraison.retrait_atelier,
            date_prevue=commande.date_livraison_prevue,
        )
        commande.livraison = livraison  # rattache des deux côtés (relation à jour)
    livraison.statut = StatutLivraison.livree
    livraison.date_effective = date_effective

    # RG20 : la commande passe à « livree »
    commande.statut = StatutCommande.livree
    commande.date_livraison_reelle = date_effective

    commentaire = "Livraison confirmée"
    if impaye:
        commentaire += f" avec solde impayé de {commande.solde} FCFA (autorisé explicitement)"
    db.add(HistoriqueStatut(
        commande_id=commande.id,
        ancien_statut=StatutCommande.terminee,
        nouveau_statut=StatutCommande.livree,
        commentaire=commentaire,
        utilisateur_id=utilisateur.id,
    ))
    db.flush()
    return commande


def lister(
    db: Session,
    statut: StatutLivraison | None,
    date_min: date | None,
    date_max: date | None,
) -> list[dict]:
    """Route 38 : tournée triée par date prévue."""
    requete = (
        select(Livraison, Commande, Client)
        .join(Commande, Commande.id == Livraison.commande_id)
        .join(Client, Client.id == Commande.client_id)
    )
    if statut is not None:
        requete = requete.where(Livraison.statut == statut)
    if date_min is not None:
        requete = requete.where(Livraison.date_prevue >= date_min)
    if date_max is not None:
        requete = requete.where(Livraison.date_prevue <= date_max)
    requete = requete.order_by(Livraison.date_prevue, Livraison.id)

    return [
        {
            "id": l.id, "commande_id": c.id, "numero_commande": c.numero,
            "client_nom": f"{cl.prenom} {cl.nom}", "client_telephone": cl.telephone,
            "solde_commande": c.solde, "mode": l.mode, "adresse": l.adresse,
            "livreur": l.livreur, "date_prevue": l.date_prevue,
            "date_effective": l.date_effective, "statut": l.statut,
        }
        for l, c, cl in db.execute(requete).all()
    ]