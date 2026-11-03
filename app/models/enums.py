import enum


# Un Enum = une liste fermée de valeurs autorisées.
# On hérite aussi de `str` pour que chaque valeur se comporte comme du texte :
# StatutCommande.en_attente == "en_attente" donne True, et FastAPI/Pydantic
# sait les convertir en JSON sans effort.

class RoleUtilisateur(str, enum.Enum):
    admin = "admin"        # le patron : tous les droits
    tailleur = "tailleur"  # mesures + production
    accueil = "accueil"    # clients, commandes, paiements, livraisons


class GenreClient(str, enum.Enum):
    homme = "homme"
    femme = "femme"
    enfant = "enfant"


# Les 8 statuts d'une commande (le workflow de la section 6).
# Le nom (à gauche) et la valeur (à droite) sont identiques : c'est
# la valeur qui sera stockée en base et affichée dans l'API.
class StatutCommande(str, enum.Enum):
    en_attente = "en_attente"
    en_coupe = "en_coupe"
    en_couture = "en_couture"
    essayage = "essayage"
    retouches = "retouches"
    terminee = "terminee"
    livree = "livree"
    annulee = "annulee"


class ModePaiement(str, enum.Enum):
    especes = "especes"
    wave = "wave"
    orange_money = "orange_money"
    virement = "virement"
    cheque = "cheque"


class ModeLivraison(str, enum.Enum):
    retrait_atelier = "retrait_atelier"  # le client vient chercher
    domicile = "domicile"                # on livre chez le client (adresse obligatoire)


class StatutLivraison(str, enum.Enum):
    planifiee = "planifiee"
    livree = "livree"