from datetime import date

from app.models.commande import Commande
from app.models.enums import StatutCommande


def est_en_retard(commande: Commande, aujourdhui: date | None = None) -> bool:
    """RG11 : date prévue dépassée et commande ni livrée ni annulée."""
    aujourdhui = aujourdhui or date.today()
    return commande.date_livraison_prevue < aujourdhui and commande.statut not in (
        StatutCommande.livree,
        StatutCommande.annulee,
    )


def vers_liste(commande: Commande) -> dict:
    """Construit un élément de CommandeListe (route 25 et 12)."""
    return {
        "id": commande.id,
        "numero": commande.numero,
        "client_id": commande.client_id,
        "client_nom": f"{commande.client.prenom} {commande.client.nom}",
        "statut": commande.statut,
        "date_commande": commande.date_commande,
        "date_livraison_prevue": commande.date_livraison_prevue,
        "montant_total": commande.montant_total,
        "montant_paye": commande.montant_paye,
        "solde": commande.solde,
        "en_retard": est_en_retard(commande),
    }