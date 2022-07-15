SPOTSCONTROLJA --- Syst�me capable de contr�ler en temps r�el des lumi�res via la connexion internet de t�l�phones portables et d'un ordinateur.



Ce syst�me � �t� d�velopp� pour les journ�es d'acceuil 2019 (Victor M, PistonII : victor.pccb@gmail.com en cas de probl�mes/questions)


	/!\    Il est bien entendu possible et m�me conseill� de modifier le code source pour corriger des probl�mes ou am�liorer l'interface et les fonctionnalit�s /!\



===========MISE EN PLACE===================


Pour faire fonctioner le syst�me, il faut lancer en premier le programme de contr�le et le tunnel tcp afin de pouvoir transmettre l'adresse � laquelle 
peuvent se connecter les t�l�phones, ensuite il suffit de placer les spots branch� sur un circuit, connect� � un t�l�phone.
	-connection du t�l�phone: il suffit de brancher le cable jack sur le circuit, d'aller ensuite sur la page www.piston.bginette.net\beta\Client.html
il faut ensuite renseigner l'adresse du programme de contr�le, que ce dernier donne dans le volet 'connexion' (il suffit d'ajouter le num�ro de port) 
ainsi que l'identifiant du spot (une clef unique qui permet au programme de contr�le de situer le spot)



===========FONCTIONNEMENT==================


1/ Principe

	les spots sont branch�s sur une rallonge sur laquelle nous avons plac� un circuit qui agit comme un interrupteur �lectronique command� par un t�l�phone portable,
qui joue donc le r�le de relais entre le programme de contr�le (ex�cut� sur un ordinateur) et les lumi�res. Cela se fait via une page Web (sur le t�l�phone) qui dialogue avec le server. 
L'ordinateur est alors capable de contr�ler l'allumage des spots en temps r�el via les t�l�phones connect�s.


2/ Programme ma�tre : server Python

Le programme est un server WebSocket, les clients Web (t�l�phones portables) s'y connectent via un tunnel tcp permettant de s'affranchir de tout probl�me de pare-feu, ISP ...
Le tunnel tcp est ouvert et h�berg� par ngrok, (https://ngrok.com/) un service gratuit, ce n'est pas le plus �l�gant car l'adresse Ip n'est pas stable (le port change � chaque fois :/ )
mais c'est la mani�re la plus simple que j'ai trouv�, de plus � la Bj aucun moyen de bidouiller le r�seau.
Le programme offre la possibilit� de contr�ler manuellement chaque spot, mais �galement de cr�er, �diter et de jouer des s�quences (menu �dition des s�quences)

  Donn�es requises pour lancer l'application:

le programme a besoin de conna�tre les identifiants et le placement des circuits (pour l'affichage des s�quences et contr�le des spots), 
il charge donc au lancement du programme un fichier .txt contenant toutes les infos sp�cifiques � un �venement (Coucher du Z ou Bapt�me).

  Pr�cisions sur ngrok :

	ngrok est un service gratuit (version limit�e, il y a une version payante) qui permet d'ouvrir des tunnels (TCP dans notre cas) c'est � dire qu'il va connecter l'adresse IP de l'ordinateur �
une adresse publique h�berg�e par leurs serveurs, en r�sum� l'entr�e du tunnel est accessible par tous depuis le Web (ce qui n'est pas le cas d'une adresse IP locale)
et celui_ci renvoie toutes les requ�tes � l'adresse locale choisie. Cela permet aux t�l�phones de se connecter � l'ordinateur h�bergeant le programme de contr�le.
	Ce service requiert d'y avoir souscrit, ainsi il y a dans la programme un "Authtoken" qui permet � ngrok d'authentifier le compte.
ATTENTION comme c'est la version gratuite un seul tunnel tcp � la fois n'est autoris�, c'est pour cela que le compte doit rester celui de ginette ( si vous utilisez 
le compte en m�me temps cela peut emp�cher l'ouverture du tunnel ...) 
 

4/ Programme Client

Le programme client est une application web (javascript) qui se connecte dans un premier temps au programme de contr�le via une WebSocket, puis re�oit de lui 
des signaux ( "on" ou "off"). Il contr�le la sortie jack du t�l�phone et ainsi envoie un signal ( +0.3V DC ) au circuit qui le d�tecte et laisse passer
le courant pour allumer le spot.



===========INSTALLATION DU PROGRAMME DE CONTROLE=================

Pour fonctionner l'application a besoin de python (version python3 ou plus) ainsi que d'une (bonne) connexion internet (elle d�termine le temps de r�ponse du programme et donc la vitesse de rafra�chissement).
D�compressez le .zip dans un dossier de votre choix, et ex�cutez SpotscontrolJA.py avec python.



==========PROBLEMES RECURENTS=============


Svp �crivez ici les probl�mes que vous avez pu rencontrer, ainsi que leur r�solution:

***SERVER PYTHON*** :

-"le tunnel tcp n'a pas pu �tre ouvert, v�rifiez votre connexion internet ou un autre processus ngrok est d�j� en cours d'�x�cution."

	-> essayer de red�marrer le tunnel (boutons start/stop tunnel dans menu connexion)
	-> si le tunnel persiste, essayer de tuer manuellemen tous les processus ngrok de votre machine : sur windows, dans le cmd en admin: "taskkill /F /IM ngrok.exe"

***CIRCUITS*** :

-Le t�l�phone est connect�, le circuit aliment�, mais lorsque le le signal est jou�, le circuit ne commute pas (pas de 'clic' du relais)

	-> Le t�l�phone n'est pas compatible, comme le fichier mp3 ne joue pas de son en soi (signal continu : DC) certains lecteurs ne sortent aucune tension en sortie..
	solution -> trouver un autre t�l�phone
		-> au niveau logiciel, trouver un moyen de contr�ler directement la tension de sortie d'un t�l�phone -> je n'ai pas r�ussi et j'en suis navr�..
	-> probl�me vient du circuit, une soudure � refaire, un composant � cram� .. -> il faut r�parer