SPOTSCONTROLJA --- Système capable de contrôler en temps réel des lumières via la connexion internet de téléphones portables et d'un ordinateur.



Ce système à été développé pour les journées d'acceuil 2019 (Victor M, PistonII : victor.pccb@gmail.com en cas de problèmes/questions)


	/!\    Il est bien entendu possible et même conseillé de modifier le code source pour corriger des problèmes ou améliorer l'interface et les fonctionnalités /!\



===========MISE EN PLACE===================


Pour faire fonctioner le système, il faut lancer en premier le programme de contrôle et le tunnel tcp afin de pouvoir transmettre l'adresse à laquelle 
peuvent se connecter les téléphones, ensuite il suffit de placer les spots branché sur un circuit, connecté à un téléphone.
	-connection du téléphone: il suffit de brancher le cable jack sur le circuit, d'aller ensuite sur la page www.piston.bginette.net\beta\Client.html
il faut ensuite renseigner l'adresse du programme de contrôle, que ce dernier donne dans le volet 'connexion' (il suffit d'ajouter le numéro de port) 
ainsi que l'identifiant du spot (une clef unique qui permet au programme de contrôle de situer le spot)



===========FONCTIONNEMENT==================


1/ Principe

	les spots sont branchés sur une rallonge sur laquelle nous avons placé un circuit qui agit comme un interrupteur électronique commandé par un téléphone portable,
qui joue donc le rôle de relais entre le programme de contrôle (exécuté sur un ordinateur) et les lumières. Cela se fait via une page Web (sur le téléphone) qui dialogue avec le server. 
L'ordinateur est alors capable de contrôler l'allumage des spots en temps réel via les téléphones connectés.


2/ Programme maître : server Python

Le programme est un server WebSocket, les clients Web (téléphones portables) s'y connectent via un tunnel tcp permettant de s'affranchir de tout problème de pare-feu, ISP ...
Le tunnel tcp est ouvert et hébergé par ngrok, (https://ngrok.com/) un service gratuit, ce n'est pas le plus élégant car l'adresse Ip n'est pas stable (le port change à chaque fois :/ )
mais c'est la manière la plus simple que j'ai trouvé, de plus à la Bj aucun moyen de bidouiller le réseau.
Le programme offre la possibilité de contrôler manuellement chaque spot, mais également de créer, éditer et de jouer des séquences (menu édition des séquences)

  Données requises pour lancer l'application:

le programme a besoin de connaître les identifiants et le placement des circuits (pour l'affichage des séquences et contrôle des spots), 
il charge donc au lancement du programme un fichier .txt contenant toutes les infos spécifiques à un évenement (Coucher du Z ou Baptême).

  Précisions sur ngrok :

	ngrok est un service gratuit (version limitée, il y a une version payante) qui permet d'ouvrir des tunnels (TCP dans notre cas) c'est à dire qu'il va connecter l'adresse IP de l'ordinateur à
une adresse publique hébergée par leurs serveurs, en résumé l'entrée du tunnel est accessible par tous depuis le Web (ce qui n'est pas le cas d'une adresse IP locale)
et celui_ci renvoie toutes les requêtes à l'adresse locale choisie. Cela permet aux téléphones de se connecter à l'ordinateur hébergeant le programme de contrôle.
	Ce service requiert d'y avoir souscrit, ainsi il y a dans la programme un "Authtoken" qui permet à ngrok d'authentifier le compte.
ATTENTION comme c'est la version gratuite un seul tunnel tcp à la fois n'est autorisé, c'est pour cela que le compte doit rester celui de ginette ( si vous utilisez 
le compte en même temps cela peut empêcher l'ouverture du tunnel ...) 
 

4/ Programme Client

Le programme client est une application web (javascript) qui se connecte dans un premier temps au programme de contrôle via une WebSocket, puis reçoit de lui 
des signaux ( "on" ou "off"). Il contrôle la sortie jack du téléphone et ainsi envoie un signal ( +0.3V DC ) au circuit qui le détecte et laisse passer
le courant pour allumer le spot.



===========INSTALLATION DU PROGRAMME DE CONTROLE=================

Pour fonctionner l'application a besoin de python (version python3 ou plus) ainsi que d'une (bonne) connexion internet (elle détermine le temps de réponse du programme et donc la vitesse de rafraîchissement).
Décompressez le .zip dans un dossier de votre choix, et exécutez SpotscontrolJA.py avec python.



==========PROBLEMES RECURENTS=============


Svp écrivez ici les problèmes que vous avez pu rencontrer, ainsi que leur résolution:

***SERVER PYTHON*** :

-"le tunnel tcp n'a pas pu être ouvert, vérifiez votre connexion internet ou un autre processus ngrok est déjà en cours d'éxécution."

	-> essayer de redémarrer le tunnel (boutons start/stop tunnel dans menu connexion)
	-> si le tunnel persiste, essayer de tuer manuellemen tous les processus ngrok de votre machine : sur windows, dans le cmd en admin: "taskkill /F /IM ngrok.exe"

***CIRCUITS*** :

-Le téléphone est connecté, le circuit alimenté, mais lorsque le le signal est joué, le circuit ne commute pas (pas de 'clic' du relais)

	-> Le téléphone n'est pas compatible, comme le fichier mp3 ne joue pas de son en soi (signal continu : DC) certains lecteurs ne sortent aucune tension en sortie..
	solution -> trouver un autre téléphone
		-> au niveau logiciel, trouver un moyen de contrôler directement la tension de sortie d'un téléphone -> je n'ai pas réussi et j'en suis navré..
	-> problème vient du circuit, une soudure à refaire, un composant à cramé .. -> il faut réparer