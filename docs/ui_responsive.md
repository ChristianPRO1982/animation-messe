# Principes fondamentaux de l'UI responsive

Ce contrat s'applique à toutes les apps Django d'Animation Messe, pour les
pages existantes et futures utilisant le panneau outils du site. Il doit être
lu avant toute création ou modification d'un template de consultation, de
liste, de formulaire ou d'administration du site.

## 1. Priorité au contenu sur smartphone

**UI-MOBILE-01** — Le repli des outils est un principe fondamental de l'UI
mobile : réduire au minimum le volume occupé en haut de la page HTML avant le
contenu principal. Les actions du panneau outils ne doivent pas former une
liste de boutons systématiquement dépliée au-dessus du contenu.

Le seuil retenu est **980 px et moins**, car le panneau mobile remplace les
panneaux latéraux à cette largeur dans le layout du site. Cette règle concerne
donc aussi certaines tablettes. À plus de 980 px, les outils restent
directement visibles dans le panneau latéral.

## 2. Équivalence entre les outils PC et mobile

**UI-MOBILE-02** — Pour une même page, un même utilisateur et un même état
métier, la zone dépliée mobile contient **tout ce que propose le panneau
outils sur PC**, dans le même ordre : liens, boutons, formulaires, séparateurs,
styles et éventuels contenus informatifs ou illustrations. Les mêmes
conditions de visibilité et de permission s'appliquent.

Il ne faut entretenir ni une sélection réduite d'actions mobiles ni une seconde
liste indépendante. Le bloc `page_tools` est l'unique source du contenu des
outils pour les deux présentations. Le titre, l'illustration et le contexte
propres au panneau mobile restent visibles hors du repli et doivent rester
concis. Le bloc `mobile_side_content` ne doit pas dupliquer les outils.

## 3. Interaction et contrat commun

**UI-MOBILE-03** — Sur mobile, une nouvelle page présente les outils fermés et
un bouton `Afficher les actions`. Un appui déplie les outils dans le flux et
remplace ce libellé par `Masquer les actions` ; un nouvel appui les replie.
L'ouverture ne déclenche ni navigation ni soumission. Aucune fermeture
automatique n'est autorisée. L'état mobile est conservé lors d'un changement
de largeur ou d'orientation ; les outils PC restent toujours visibles.

Les panneaux contenant seulement des informations ou illustrations suivent le
même principe. Un panneau outils vide ne présente pas de bouton de repli.

**UI-MOBILE-04** — Le mécanisme est centralisé dans `templates/base.html`,
`static/js/base.js` et les styles communs. Le même conteneur DOM est déplacé
entre les panneaux, sans clonage. Les identifiants, gestionnaires
d'événements, protections CSRF et attributs de soumission, notamment `form`,
`name` et `value`, sont conservés. Les confirmations continuent de passer par
la [message box commune](popup_messagebox.md).

**UI-MOBILE-05** — Le contrôle est un vrai `<button type="button">`, avec
`aria-expanded` synchronisé et `aria-controls` visant un identifiant unique.
Les outils repliés sont réellement masqués avec `hidden`, y compris pour la
navigation clavier ; les règles CSS de disposition ne doivent pas neutraliser
ce masquage. Le focus reste accessible après un changement de panneau. Les
libellés sont traduits par Django et transmis au JavaScript par le template.
Sans JavaScript, les outils restent directement accessibles.

Les thèmes existants, les modes clair et sombre et les styles des actions
doivent être préservés. Ce contrat porte sur les panneaux outils du site ; il
ne demande pas de replier le contenu principal, les documents générés, les
e-mails ou l'administration Django native.

## 4. Application app Django par app Django

Chaque document `functional_requirements.md` précise l'application de ce
contrat à son périmètre :

- [app_main](app_main/functional_requirements.md) : socle commun, accueil,
  connexion, compte, préférences et administration du site ;
- [app_member](app_member/functional_requirements.md) : profil, préférences et
  gestion des rôles globaux, y compris via la page compte de `app_main` ;
- [app_group](app_group/functional_requirements.md) : groupes, listes,
  tableau de bord et toutes les pages dédiées de gestion, recueil compris ;
- [app_planning](app_planning/functional_requirements.md) : pages de calendrier,
  tableau de planning et workflows de génération ou de validation ;
- [app_celebration](app_celebration/functional_requirements.md) : consultation,
  édition, gabarits, validations et feuilles de messe ;
- [app_email](app_email/functional_requirements.md) : commandes présentées dans
  les pages du site, notamment les paramètres d'envoi dans `app_main`.

Toute nouvelle app proposant un panneau outils doit reprendre ce contrat dans
ses exigences fonctionnelles et utiliser le mécanisme commun.

## 5. Vérification avant livraison d'un écran

Vérifier les largeurs 390, 768, 980 et 981 px, les changements d'orientation,
le clavier et les différents rôles autorisés sur la page. Comparer le contenu
des outils PC à celui de la zone mobile dépliée : aucune action manquante,
aucun doublon visible, mêmes séparateurs et mêmes soumissions. Vérifier les
confirmations, les traductions, les quatre thèmes et les panneaux vides ou
informatifs. Le contenu principal doit rester rapidement accessible lorsque
les outils sont repliés.
