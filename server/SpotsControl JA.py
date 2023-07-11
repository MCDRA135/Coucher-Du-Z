# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 21:56:58 2019

@author: Victor Morand - PistonII
Ce programme est destiné à commander l'allumage des lumières
du batiment Sainte Geneviève pendant la cérémonie du coucher du Z (et du baptême)
"""

import time
import tkinter as tk
import tkinter.ttk as ttk
import os ,sys
sys.path.append(os.path.join(sys.path[0],'libs'))
from tkinter import messagebox
from tkinter import font
import copy
import numpy as np
from websocket_server import WebsocketServer
from threading import Thread
from pyngrok import conf, ngrok
import signal

#Fonction globales :

conf.get_default().ngrok_version = "v2"
conf.get_default().auth_token = '2OhNpvcigbHLXSWpKExHqxr90uk_5baFmnqzUqTsD7ewpByTn' # "287KWQBQVOLvlNFDpJNgmYdDGlv_7HnovYhWfUVUViTPEmfnQ"
conf.get_default().region = "eu"

def ChooseEvent():
    """ouvre une fenêtre qui permet de choisir quelles données utiliser, en fonction de la cérémonie"""

    eventList = ''

    class chooseFrame(tk.Frame):
        
        def __init__(self, fenetre, **kwargs):
            tk.Frame.__init__(self, fenetre, **kwargs)
            self.eventListbox = tk.Listbox(self, listvariable= tk.StringVar(self,value = eventList),width = 35, height = eventList.count(' '),
                                             activestyle = 'underline', selectmode = tk.SINGLE, font = listFont)
            self.eventListbox.pack(padx= 5, pady = 10)
            self.eventListbox.selection_set(1)
            self.eventListbox.bind("<<ListboxSelect>>",self.UpdateName)
            
            self.runButton = tk.Button(self, text = "Lancer le programme", relief= 'groove',activebackground ='#44F',
                                  takefocus =0,background = '#69F', width = 20, height =2, command = fenetre.quit)
            self.runButton.pack(pady=10)

        def UpdateName(self,event):
            self.eventName = self.eventListbox.get(self.eventListbox.curselection())
            

    listFiles = os.listdir('Cérémonies') #on récupère la liste des fichiers présents dans 'Cérémonies'
    for fileName in listFiles:
        if fileName[-4:] == '.txt':
            eventList += ' ' + fileName[:-4]


    fenetre = tk.Tk(className = "Choisir un évenement")
    
    listFont = font.Font(family='Constantia',size =10, weight='bold')
    fenetre.iconbitmap('logoBj.ico')
    
    frame = chooseFrame(fenetre)
    frame.pack()

    
    
    fenetre.mainloop()
    
    try :
        eventName = frame.eventListbox.get(frame.eventListbox.curselection())
        fenetre.destroy()
    except:
        eventName = 'end'       #Si jamais l'utilisateur quitte l'application..
    
    
    return eventName



def GetInfos(eventName):
    """récupère les informations nécésaires au programme et spécifiques à une cérémonie,
cellNames est une matrice 3*6, contenant les identifiants """
    def GetValue(row):
        if ":" in row:
            for i in range(len(row)):
                if row[i]==":":
                    res = row[i+1:]
                    return res
        return None
    dataPath = 'Cérémonies/'+eventName+'.txt'
    infos = {}
    
    idFile = open(dataPath, 'r')
    contend = idFile.read()
    idFile.close()

    contend = contend.split('\n')
    cellNames = contend[5:]
    cellNames = [row.replace(' ','').split(',') for row in cellNames]

    infos['eventName'] = eventName
    infos['cellNames'] = cellNames
    infos['label'] = GetValue(contend[0])
    infos['width'] = int(GetValue(contend[1]))
    infos['height'] = int(GetValue(contend[2]))
    infos['padding'] = int(GetValue(contend[3]))
    
    return infos


def DrawLights(canvas):
    """fonction dessinant les lumières allumées ou éteintes """
    for i in range(len(sgmap)):
        for j in range(len(sgmap[0])):
            if sgmap[i][j] == 1:
                color = '#FE8'
            else :
                color = '#999'
            canvas.itemconfigure(canvas.rectangles[i][j], fill=color )
    canvas.update()

def switchLight(i,j):
    """allume ou éteint la lumière dans la cellule de coord i,j"""
    sgmap[i][j] = 1- sgmap[i][j]
    return

def GetSequenceList(eventName):
    """Met a jour la liste des séquences dispos pour l'événement indiqué"""
    sequenceList = ''
    extension = ' - '+eventName+'.txt'
    listFiles = os.listdir('Sequences')      #on récupère la liste des fichiers présents dans 'Sequences'
    for fileName in listFiles:
        if extension in fileName:
            sequenceList += ' ' + fileName.replace(extension,'')
    return sequenceList

def GetSequence(name,eventName):
    """renvoie la séquence nomée en lisant dans le fichier 'sequences' """
    sequ = []
    filepath = "Sequences\\" + name +' - '+eventName+'.txt'
    
    #on charge la séquence choisie
    
    file = open(filepath,'r')
    contend = file.read()
    file.close

    # on traite le contenu pour qu'il soit lisible
    
    contend = contend.replace('\n','')
    contend = contend.replace('[','')
    contend = contend.split('*')
    contend.pop(-1)
    contend = [frame.split(']') for frame in contend]
    for row in contend:
        row.pop(-1)

    for frame in contend:
        sequ.append([[int(i)for i in row.split(',')] for row in frame])

    return sequ


def UpdateLights(frame= [] , x =0 ,y = 0):
    """Fonction permettant la mise à jour des lumières"""
    global sgmap
    global server
    
    if frame != []:
        sgmap = frame
    else:
        switchLight(y,x)
        
    if len(server.clients) == 0:
        return
    client = server.clients[0]
    for i in range(len(sgmap)):
        for j in range(len(sgmap[0])):
            if cellId[i][j] != 0:
                for cli in server.clients:
                    if int(cli['id']) == cellId[i][j]:
                        client = cli
                if sgmap[i][j] == 1:
                    server.send_message(client,"on" + client["name"])
                else:
                    server.send_message(client,"off" + client["name"])
                            
    
#============= création des classes ================
 
class Interface(tk.Frame):
    
    """Fenêtre principale.
    Tous les widgets sont stockés comme attributs de cette fenêtre. on donne également les dimensions des fenêtres à dessiner"""
    
    def __init__(self, fenetre,infos, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self.grid()
        self.numFrame = 0
        self.playSpeed = 5  #vitesse de lecture des séquences en fps
        self.testSpeed = 5
        self.eventName = infos['eventName']
        
        # Création des widgets
        
        self.w = MainCanvas(fenetre,infos)
        self.w.grid(column=1,row = 0)

        self.note = ttk.Notebook( width = 300, height = 550)
        self.note.grid(column = 0,row=0)

        self.tab1 = tk.Frame(self.note) 

        # widgets dans la tab1

        self.message = tk.Label(self.tab1, text=" Interface de commande des lumières \n " ,
                                justify = tk.CENTER, font= TitleFont)
        self.message.pack(fill = 'x', pady = 10)

        self.resetButton = tk.Button(self.tab1, text = "Eteindre tout (esc)", width = 50, pady = 5, relief= 'groove',command = self.w.reset, takefocus =0)
        self.resetButton.pack(fill = 'x' , pady = 15)
        
        self.seqFrame = ttk.LabelFrame(self.tab1, text = 'Jouer une Séquence', borderwidth = 1, labelanchor = 'n', height = 60)
        self.seqFrame.pack(fill= 'x' , padx= 5, pady = 20, ipady=10)
        
        self.seqList = tk.Listbox(self.seqFrame, listvariable= tk.StringVar(self,value = sequenceList),width = 50, height = 5,
                                  activestyle = 'underline', selectmode = tk.SINGLE, font = sequenceFont)
        self.seqList.pack(padx= 5, pady = 10)

        self.PlaySpeedScale = tk.Scale(self.tab1, orient=tk.HORIZONTAL, cursor = 'hand1',from_ = 1 ,to = 30,sliderlength = 20
                                   ,resolution = 0.25, label = 'Vitesse de la séquence ', command = self.ChangeSpeed )
        self.PlaySpeedScale.set(self.playSpeed)
        self.PlaySpeedScale.pack(pady=5, fill ='x')

        self.deleteButton = tk.Button(self.seqFrame, text = "Supprimer Séquence", relief= 'groove',activebackground ='#F44',takefocus =0
                                      ,background = '#F66', command = self.DeleteSequence )
        self.deleteButton.pack(pady=10, anchor = 'ne')
        
        self.launchButton = tk.Button(self.seqFrame, text = "Lancer Séquence", relief= 'groove',activebackground ='#44F',takefocus =0
                                      ,background = '#69F', width = 20, height =2, command = self.LaunchSequence )
        self.launchButton.pack(pady=10)

        
        self.tab2 = tk.Frame(self.note)

        # widgets dans la tab2

        self.message = tk.Label(self.tab2, text="Interface de création des \n séquences" ,
                                justify = tk.CENTER, font= TitleFont)
        self.message.pack(fill = 'x', pady=10)

        self.resetButton = tk.Button(self.tab2, text = "Eteindre tout (esc)", width = 50, pady = 5, relief= 'groove',command = self.w.reset ,takefocus =0)
        self.resetButton.pack(fill = 'x' , pady = 15 ,padx =10)

        self.nameFrame = ttk.LabelFrame(self.tab2, text = 'Nom de la séquence', borderwidth = 1, height = 60)
        self.nameFrame.pack(fill= 'x' , padx= 5, pady = 5)

        self.seqName = tk.Entry(self.nameFrame)
        self.seqName.pack(padx= 5, pady = 5)

        self.seqEditList = tk.Listbox(self.tab2, listvariable= tk.StringVar(self,value = sequenceList),width = 50, height = 5,
                                  activestyle = 'underline', selectmode = tk.SINGLE, font = sequenceFont)
        self.seqEditList.pack(padx= 5, pady = 5)
        self.seqEditList.bind("<<ListboxSelect>>",self.EditSequ)
        
        
        self.txt = tk.Label(self.tab2, text="Frame n°1/1" ,
                                justify = tk.CENTER)
        self.txt.pack(fill = 'x', pady=5)

        self.playFrame = tk.Frame(self.tab2)
        self.playFrame.pack(pady = 5)

        self.prevFrame = tk.Button(self.playFrame, text ='<<', relief= 'groove', command = self.ClickPrev )
        self.prevFrame.grid(row= 0 ,column = 0, padx = 2)
        
        self.nextFrame = tk.Button(self.playFrame,text = '>>', relief= 'groove', command = self.ClickNext )
        self.nextFrame.grid(row= 0 ,column = 2 , padx = 2)

        self.playSequ = tk.Button(self.playFrame,text = 'Jouer', relief= 'groove', command = self.PlaySequ )
        self.playSequ.grid(row= 0 ,column = 1 , padx = 2)


        self.TestSpeedScale = tk.Scale(self.tab2, orient=tk.HORIZONTAL, cursor = 'hand1',from_ = 1 ,to = 30,sliderlength = 20
                                   ,resolution = 0.25, label = 'Vitesse de la séquence ', command = self.ChangeTestSpeed )
        self.TestSpeedScale.set(self.testSpeed)
        self.TestSpeedScale.pack(pady=10, fill ='x')

        self.resetButton = tk.Button(self.tab2, text = "Recommencer", width = 50, pady = 5, relief= 'groove',command = self.ClearSequence
                                     ,activebackground ='#F33' )
        self.resetButton.pack(fill = 'x' , pady = 15, padx = 10)

        self.SaveButton = tk.Button(self.tab2, text = "Enregistrer Séquence", width = 50, pady = 5, relief= 'groove',command = self.SaveSequence
                                     ,background = '#69F',activebackground ='#44F' )
        self.SaveButton.pack(fill = 'x' , pady = 15, padx = 10)


        self.tab3 = tk.Frame(self.note)

        # widgets dans la tab3 - interface de connexion

        self.message = tk.Label(self.tab3, text="Interface de contôle de connexion \navec les Clients" ,
                                justify = tk.CENTER, font= TitleFont)
        self.message.pack(fill = 'x', pady=10)

        self.TunnelInfo = tk.Label(self.tab3, text="Etat du tunnel tcp : \n Non connecté" ,bd=1, relief= 'groove',
                                justify = tk.LEFT,wraplength =  500, font = InfoFont)
        self.TunnelInfo.pack(fill = 'x', pady=10)

        self.CFrame = tk.Frame(self.tab3)
        self.CFrame.pack(pady = 20)

        self.ConnectButton = tk.Button(self.CFrame, text ='Start tunnel', relief= 'groove', command = self.StartTunnelClick )
        self.ConnectButton.grid(row= 0 ,column = 0, padx = 2)
        
        self.DisconnectButton= tk.Button(self.CFrame,text = 'Stop Tunnel', relief= 'groove', command = self.KillTunnelClick )
        self.DisconnectButton.grid(row= 0 ,column = 2 , padx = 2)



        #puis on ajoute les pages au notebook
        
        self.note.add(self.tab1, text ="Commande")
        self.note.add(self.tab2, text ="Editer Séquences")
        self.note.add(self.tab3, text ="Connexion")

        
        #création des évenements clavier
        self.bind_all('<Right>', self.ClickNext )
        self.bind_all('<Left>', self.ClickPrev)
        self.bind_all('<Escape>', self.w.reset)
  
    def UpdateTunnelInfo(self,text):
        self.TunnelInfo.configure(text = "Etat du tunnel tcp : \n"+text)

    def StartTunnelClick(self):
        global tunnel
        global tunnelOpen
        tunnelOpen = CreateNewTunnel(self,tunnel)

    def KillTunnelClick(self):
        global tunnel
        KillTunnel(self,tunnel)
        
        
    
    def ClickNext(self,event = None):
        global sgmap
        global sequence
        
        sequence[self.numFrame] = copy.deepcopy(sgmap)
        
        self.numFrame += 1
        
        if self.numFrame == len(sequence):
            sequence.append(copy.deepcopy(sgmap))
        else:
            UpdateLights(frame = copy.deepcopy(sequence[self.numFrame]))
        
        self.txt["text"] = "Frame n° {}".format(self.numFrame+1)+"/{}".format(len(sequence))
        DrawLights(self.w)
        

    
    def ClickPrev(self, event= None):
        global sgmap
        global sequence
        
        sequence[self.numFrame] = copy.deepcopy(sgmap)
                
        if self.numFrame > 0:
            self.numFrame += -1

        UpdateLights(frame = copy.deepcopy(sequence[self.numFrame]))
        
        self.txt["text"] = "Frame n° {}".format(self.numFrame+1)+"/{}".format(len(sequence))
        DrawLights(self.w)

    def PlaySequ(self):
        """joue la séquence en cours d'édition"""
        global sequence
        global sgmap
        begin = time.time()
        for i in range(len(sequence)):
            UpdateLights(frame = copy.deepcopy(sequence[i]))
            self.numFrame = i
            self.txt["text"] = "Frame n° {}".format(i+1)+"/{}".format(len(sequence))
            DrawLights(self.w)
            time.sleep((1/(self.testSpeed+0.1)))
            
    def LaunchSequence(self):
        """Lance la séquence sélectionée"""
        global sgmap
        
        selectId = self.seqList.curselection()
        
        if selectId ==():
            messagebox.showerror(title ='Erreur', message = "Aucune Séquence sélectionnée !")
            return
        name = self.seqList.get(selectId[0])
        sequ = GetSequence(name,self.eventName)
        
        #on lance la séquence
 
        for i in range(len(sequ)):
            UpdateLights(frame = copy.deepcopy(sequ[i]))
            DrawLights(self.w)
            time.sleep((1/(self.playSpeed+0.1)))


    def EditSequ(self,event):
        global sequence
        
        self.seqName.delete(0,100)
        try:
            selectId = self.seqEditList.curselection()
            name = self.seqEditList.get(selectId[0])
            self.seqName.insert(0,name)
        except:
            return
        sequence = GetSequence(name, self.eventName)
        UpdateLights(sequence[0])
        self.numFrame = 0
        self.txt["text"] = "Frame n° {}".format(self.numFrame+1)+"/{}".format(len(sequence))
        DrawLights(self.w)
        
        
    def ChangeTestSpeed(self,value):
        self.testSpeed = self.TestSpeedScale.get()

    def ChangeSpeed(self,value):
        self.playSpeed = self.PlaySpeedScale.get()

    def ClearSequence(self):
        global Ncol
        global Nrow
        global sequence
        global sgmap

        self.seqName.delete(0,100)
        sequence = [ [[0]*Ncol for i in range(Nrow)] ]
        UpdateLights(frame = [[0]*Ncol for i in range(Nrow)])
        self.numFrame = 0
        self.txt["text"] = "Frame n° {}".format(self.numFrame+1)+"/{}".format(len(sequence))
        DrawLights(self.w)


    def DeleteSequence(self):
        """Supprime séquence sélectionée"""

        selectId = self.seqList.curselection()
        
        if selectId ==():
            messagebox.showerror(title ='Erreur', message = "Aucune Séquence sélectionnée !")
            return
        name = self.seqList.get(selectId[0])
        filepath = 'Sequences/' + name + ' - ' + self.eventName + '.txt'
        if messagebox.askokcancel(title="Confirmer la suppression",
                                  message  = "Etes-vous sûr de vouloir supprimer la séquence '"+name+"' ?") == False:
            return
        os.remove(filepath)
        sequenceList = GetSequenceList(self.eventName)
        self.seqList['listvariable']= tk.StringVar(self,value = sequenceList)
        self.seqEditList['listvariable']= tk.StringVar(self,value = sequenceList)
        

    def SaveSequence(self):
        global sequence
        global sequenceList

        name = self.seqName.get()
        name = name.replace(' ','_')
        name = name.replace('/','')
        name = name.replace('\\','')
        if name == '':
            messagebox.showerror(title ='Erreur', message = "Il faut un nom de séquence !")
            return
        if len(sequence) == 1:
            messagebox.showerror(title ='Erreur', message = "La séquence ne contient qu'une seule frame !")
            return
        path = 'Sequences/' + name + ' - ' + self.eventName + '.txt'
        newFile = open(path, 'w')

        
        for i in range(len(sequence)):
            for j in range(len(sequence[0])):
                newFile.write(str(sequence[i][j]))
                newFile.write('\n')
            newFile.write('\n*\n')
            
        newFile.close
        self.ClearSequence()
        self.seqName.delete(0,50)
        sequenceList = GetSequenceList(self.eventName)
        self.seqList['listvariable']= tk.StringVar(self,value = sequenceList)
        self.seqEditList['listvariable']= tk.StringVar(self,value = sequenceList)
        messagebox.showinfo(title = "succès" , message = "La séquence a  étée enregistrée avec succès !")
                  
# définition de la zone de dessin principale (canvas)
     
class MainCanvas(tk.Canvas):
    """zone de dessin centrale"""
    
    def __init__(self, fenetre,infos,**kwargs):
        self.GridPos = [3,100]
        self.wid = infos['width']                   # largeur des fenêtre (px)
        self.hei = infos['height']                  # hauteur des fenêtres (px)
        self.offset = infos['padding']              # espace entre les fenêtres (px)
        self.label = infos['label']
        self.cellNames = infos['cellNames']
        self.rectangles = [[0]*Ncol for i in range(Nrow)]
        self.infoTriangle = [[0]*Ncol for i in range(Nrow)]
        tk.Canvas.__init__(self, width = 1 + (self.wid + self.offset)*Ncol,
                                 height = 110+ (self.hei+ self.offset)*Nrow   , bd = 1,bg = '#111',cursor ='crosshair', **kwargs)
        self.create_text((1 + (self.wid + self.offset)*Ncol)/2,30, text= self.label , font= canvasTitleFont, fill = "#FFF")
        
        for i in range(Nrow):
            for j in range(Ncol):
                X = self.GridPos[0]+ self.offset/2 + (self.wid + self.offset)*j
                Y = self.GridPos[1]+ self.offset/2 + (self.hei + self.offset)*i
                self.rectangles[i][j] = self.create_rectangle(X, Y, X+ self.wid ,Y + self.hei, fill = '#777')

                if self.cellNames[i][j] != 'void':
                    self.infoTriangle[i][j] = self.create_polygon(X + self.wid ,Y + self.hei,
                                                                  X + self.wid ,Y + self.hei -15,
                                                                  X + self.wid -20,Y + self.hei ,
                                                                  fill = '#F00', outline = '#000' , joinstyle = tk.ROUND)
                    self.create_text( X + self.wid*0.3 ,Y +self.hei-7, text = self.cellNames[i][j])
        DrawLights(self)
        self.bind("<Button-1>",self.CanvasClick)
        
    def CanvasClick(self,event):
        """lorsque l'on clique sur une fenêtre, on change l'état de la lumière"""

        if event.x >= self.GridPos[0] and event.x <= self.GridPos[0]+ (self.wid+self.offset)*Ncol and event.y >= self.GridPos[1] and event.y <= self.GridPos[1] + (self.offset + self.hei)*Nrow :
            winX = int((event.x - self.GridPos[0])/(self.wid+self.offset)) 
            winY = int((event.y - self.GridPos[1])/(self.hei+ self.offset))
            if self.cellNames[winY][winX] == 'void':
                return
            UpdateLights(x = winX, y = winY )
        DrawLights(self)
        
    def reset(self, event =None):
        """remet la matrice à 0"""
        global sgmap
        Zeroframe = [[0 for j in range(len(sgmap[0]))] for i in range(len(sgmap))]
        UpdateLights(frame = Zeroframe)
        DrawLights(self)

# thread faisant tourner le server en parallèle

class HostingServerLoop(Thread):
    """thread tournant en boucle permettant de gérer les connection en parallèle du programme principal"""

    def __init__(self,server):
        Thread.__init__(self)
        self.serverToRun = server

    def run(self):
        """code qui s'exécute en // """
        self.serverToRun.run_forever()
        
    def stop(self):
        """stoppe le server"""
        self.serverToRun.shutdown()

# lorsqu'un client se connecte (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	


# Called for every client disconnecting
def client_left(client, server):
    global cellId
    global interface
    global running
    print("Client(%d) disconnected" % client['id'])
    if running == False:
        return
    for i in range(len(cellId)):
        for j in range(len(cellId[0])):
            if cellId[i][j] == int(client['id']):
                cellId[i][j] = 0
                interface.w.itemconfigure(interface.w.infoTriangle[i][j] , fill = '#F00')
    print(np.array(cellId))
    


# lorsqu'un client envoie un message, ie lors de la connexion
def message_received(client, server, message):
    global interface
    global Nrow
    global Ncol
    if len(message) > 200:
            message = message[:200]+'..'
    print("Client(%d) said: %s" % (client['id'], message))

    if message[:4] == "id =":
        name = message[4:]
        for i in range(Nrow):
            for j in range(Ncol):
                if name == infos['cellNames'][i][j]:
                    cellId[i][j] = int(client['id'])
                    client["name"] = name ## Le nom correspond à l'id de piaule
                    interface.w.itemconfigure(interface.w.infoTriangle[i][j] , fill = '#0F0')
                    print(np.array(cellId))
                    UpdateLights(frame = sgmap)
                    return
        print("identifiant non reconnu")
        server.send_message(client,'identifiant non reconnu')
                
            
    if message == "KeepAlive":
        server.send_message(client,'KeepAlive')
    return
    

    
#fonction appelée lors de la fermeture de la fenêtre
def OnClosing():
    global server
    global running
    global tunnelOpen
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        running = False
        server.send_message_to_all("end")
        time.sleep(0.5)     
        server.__exit__()                           # on ferme le server (et le port avec :) )
        threadServer.stop()                         # on tue la boucle du server
        fenetre.destroy()
        if tunnelOpen:
            ngrok.kill()

def CreateNewTunnel(interface, tunnel):
    """crée un nouveau tnnel tcp avec ngrok et update les infos, renvoie true si le tunnel fonctionne"""
    URL = ngrok.connect(addr=PORT, proto='tcp') # CDZ 2023: changé cette ligne, apparemment "port=PORT" ne permettait pas de passer le port à la config du tunnel (changement de version entre-temps)
    tunnel = ngrok.get_tunnels()[0]
    print(tunnel)
    print("tunnel tcp crée : "+tunnel.__str__())
    interface.UpdateTunnelInfo("Adresse :  "+tunnel.public_url + "\nproto : "+tunnel.proto+"\nforward to -> localhost:"+str(PORT))
    return True
    # try:
    #     URL = ngrok.connect(port=PORT, proto='tcp')
    # except:
    #     print("le tunnel tcp n'a pas pu être ouvert, vérifiez la connexion internet, ou un processus ngrok est déjà lancé")
    # else:
    #     tunnel = ngrok.get_tunnels()[0]
    #     print("tunnel tcp crée : "+tunnel.__str__())
    #     interface.UpdateTunnelInfo("Adresse :  "+tunnel.public_url + "\nproto : "+tunnel.proto+"\nforward to -> localhost:"+str(PORT))
    #     return True

def KillTunnel(interface, tunnel):
    """tue tout process ngrok"""
    ngrok.kill()
    interface.UpdateTunnelInfo("Non Connecté")
    return
    
def CloseApp(signal,frame):
    """fonction appelée lors de la fermeture du programme"""
    global server
    global running
    global tunnelOpen
    running = False
    server.send_message_to_all("end")
    print("Fermeture de l'application")
    time.sleep(0.5)
    server.__exit__()                               # on ferme le server (et le port avec :) )
    threadServer.stop()                             # on tue la boucle du server
    fenetre.destroy()
    if tunnelOpen:
        ngrok.kill()





##################################################################################################################

###################################### DEBUT DU PROGRAMME PRINCIPAL ##############################################

##################################################################################################################




#Tout d'abord on demande à l'utilisateur de choisir une cérémonie parmi celles disponibles


eventName = ChooseEvent()
if eventName =='end':
    sys.exit(0)                                     #on arrête l'app si la fenêtre de dialogue a étée détruite
else:
    print(60*'#'+'\n\n'+' Execution du Programme de la Cérémonie :  '+eventName+'\n\n'+60*'#'+'\n\n')

# variables gloabales

running = True

infos = GetInfos(eventName)                         #on récupère toutes les infos nécéssaires , spécifiques à la cérémonie

Nrow = len(infos['cellNames'])                      #format du tableau avec lequel nous allons travailler
Ncol = len(infos['cellNames'][0])

cellId = [[0]*Ncol for i in range(Nrow)]            #matrice servant a stocker le numéro des clients se connectant au serveur en fonction de l'indentifiant qu'ils ont communiqué


sgmap = [[0]*Ncol for i in range(Nrow)]
sequence = [ [[0]*Ncol for i in range(Nrow)] ]

tunnelOpen = False


# on charge la liste des séquences disponibles   
        
sequenceList = GetSequenceList(eventName)

# on lance le serveur
PORT = 8080

# * CHANGEMENT EFFECTUE A CETTE LIGNE
server = WebsocketServer(host='0.0.0.0', port=PORT)      #attention si l'on ne spécifie pas 'host' le server sera lancé en local seulement !
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)

threadServer = HostingServerLoop(server)
threadServer.start()                                # on lance le server qui s'occuppe d'acceuillir nos clients

 
#on crée la fenêtre

fenetre = tk.Tk(className = "Panneau de contrôle")
fenetre.iconbitmap('logoBj.ico')
fenetre.protocol("WM_DELETE_WINDOW", OnClosing)

signal.signal(signal.SIGINT, CloseApp)              #en cas d'interruption externe du programme, on ferme tout proporement

#edition des polices utilisées :

TitleFont = font.Font(family='Constantia', size=12, weight='bold')
InfoFont = font.Font(family = 'Consolas', size = 10, weight='bold')
sequenceFont = font.Font(family='Constantia',size =10, weight='bold')
canvasTitleFont = font.Font(family='impact', size=18)

#on crée l'interface principale

interface = Interface(fenetre, infos)


# Ouverture d'un tunnel tcp avec ngrok (https://ngrok.com/), cela permet d'accéder au serveur quelle que soit la connexion Internet
#  et cela sans aucun port forwarding ! en revanche le numéro de port change à chaque fois, il faut le communiquer pour permettre aux téléphones de se connecter

print('\nlancement de ngrok ... \n')

ngrok.kill()
tunnel = []
tunnelOpen = CreateNewTunnel(interface, tunnel)


# on lance la boucle !

interface.mainloop()

