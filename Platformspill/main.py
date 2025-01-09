import pygame
import sys
import random

BREDDE, HOYDE = 1600, 600  #Setter dimensjonene til vinduet
FPS = 60  #Antall frames per sekund
GRAVITASJON = 0.5  #Hvor raskt figuren faller mot bakken
HOPPEKRAFT = 10  #Hvor høyt figuren hopper
SKADE_RADIUS = 100  #Radius for skade ved abilities
SIKKER_RADIUS = 300  #Minimumsavstand for fiendes spawning i forhold til deg
EVNE_VARIGHET = 30  #Hvor lenge spesialevnen varer
COOLDOWN_E = 180  #Cooldown for E-ability i frames
COOLDOWN_Q = 120  #Cooldown for Q-ability i frames
PROSJEKTIL_FART = 10  #Hvor raskt prosjektiler beveger seg
PROSJEKTIL_BREDDE, PROSJEKTIL_HOYDE = 150, 20  #Dimensjonene til prosjektilene
NIVA_VARIGHET = 20 * FPS  #Tiden hvert nivå varer (i frames)
FIENDE_SPAWN_INTERVALL = 180  #Antall frames mellom hver fiendes spawning

#starter Pygame greia
pygame.init()
skjerm = pygame.display.set_mode((BREDDE, HOYDE))  #Lager vinduet
pygame.display.set_caption("Plattformspill")  #Tittel til vinduet
klokke = pygame.time.Clock()  #Holder styr på tiden

#Henter bildet til figuren vår, bytt sti hvis det trengs
figur_bilde = pygame.image.load(r'C:\Users\jeppe\.vscode\gem-slot-game\src\sprite.png')
figur_bilde = pygame.transform.scale(figur_bilde, (50, 100))  #Gjør bildet mindre 

#Dette er figuren 
figur_rekt = figur_bilde.get_rect()  #Får en rektangel som representerer figuren
figur_rekt.x = 100  #Startposisjon for figuren på x-aksen
figur_rekt.y = HOYDE - 150  #Litt over bakken
figur_fart_y = 0  #Fart i y-retning
pa_bakken = True  #Sjekk om figuren er på bakken

#Bakken
bakke_rekt = pygame.Rect(0, HOYDE - 50, BREDDE, 50) 

#Poeng og helse
poeng = 0  #Start med null poeng
spiller_helse = 100  #Start med full helse

#Vise poeng og greier på skjermen
def vis_ui(poeng, cooldown_e, cooldown_q, niva):
    #Viser info på skjermen
    font = pygame.font.Font(None, 36)  #
    poeng_tekst = font.render(f'Poeng: {poeng}', True, (255, 255, 255))  #Gjør teksten hvit
    niva_tekst = font.render(f'Nivå: {niva}', True, (255, 255, 255))  #Viser hvilket nivå du er på
    skjerm.blit(poeng_tekst, (10, 10))  #Plasser oppe til venstre
    skjerm.blit(niva_tekst, (BREDDE - niva_tekst.get_width() - 10, 10))  #Oppe til høyre

    #Vis cooldowns også
    cooldown_tekst_e = font.render(f'Evne E: {cooldown_e // FPS}', True, (255, 255, 255))
    cooldown_tekst_q = font.render(f'Evne Q: {cooldown_q // FPS}', True, (255, 255, 255))
    skjerm.blit(cooldown_tekst_e, (10, 50))
    skjerm.blit(cooldown_tekst_q, (10, 90))

#Klassen for fiender
class Fiende:
    def __init__(self, x, y, retning):
        #Initierer fiender med posisjon og retning
        self.rekt = pygame.Rect(x, y, 50, 50)  #Bare en firkant for nå
        self.helse = 100  #Hvor mye helse fienden har
        self.retning = retning  #1 er høyre, -1 er venstre
        self.fart = 2  #Hvor raskt fienden beveger seg

    def oppdater(self):
        #Flytter fienden i sin retning
        self.rekt.x += self.retning * self.fart
        #Hvis den treffer kanten, snu 
        if self.rekt.left < 0 or self.rekt.right > BREDDE:
            self.retning *= -1

    def tegn(self):
        #Tegner fienden som en rød firkant
        pygame.draw.rect(skjerm, (255, 0, 0), self.rekt)  

    def ta_skade(self, skade):
        #dreper fienden hvis helsen går under null
        self.helse -= skade
        if self.helse <= 0:
            self.do()

    def do(self):
        #Slett fienden 
        pass

class Prosjektil:
    def __init__(self, x, y, retning):
         #Initierer prosjektiler med posisjon og retning
        self.rekt = pygame.Rect(x, y, PROSJEKTIL_BREDDE, PROSJEKTIL_HOYDE)
        self.retning = retning

    def oppdater(self):
        # Flytter prosjektilene
        self.rekt.x += self.retning * PROSJEKTIL_FART

    def tegn(self):
        # egner prosjektilene som blå rektangler
        pygame.draw.rect(skjerm, (0, 0, 255), self.rekt)  

# Spawn fiender trygt (ikke rett oppi spilleren)
def spawn_fiende_trygt(spiller_x, spiller_y):
    # Sørger for at fiender ikke spawner rett ved spilleren
    while True:
        x_posisjon = random.randint(100, BREDDE - 100)
        y_posisjon = HOYDE - 100
        if abs(x_posisjon - spiller_x) > SIKKER_RADIUS:
            return Fiende(x_posisjon, y_posisjon, random.choice([1, -1]))

#spillets hovedløkke
def hoved():
    global figur_fart_y, pa_bakken, poeng, spiller_helse, evne_aktiv, evne_teller, kjolenedteller_e, kjolenedteller_q, siste_retning, niva, niva_teller
    fiender = [spawn_fiende_trygt(figur_rekt.x, figur_rekt.y)]  #Starter med en fiende
    prosjektiler = []  #Liste over alle aktive prosjektiler
    fiende_spawn_teller = 0  #Telle hvor mange frames siden sist spawn
    figur_fart_x = 5  #Hastigheten figuren kan bevege seg i sidene
    niva = 1  #Startnivå
    niva_teller = 0  #Telle frames for nivåøkning
    siste_retning = 1  #Hvilken vei figuren ser

    #Start cooldown greiene
    kjolenedteller_e = 0  #Cooldown-teller for E-evnen
    kjolenedteller_q = 0  #Cooldown-teller for Q-evnen
    evne_aktiv = False  #Om spesialevnen er aktiv
    evne_teller = 0  #Hvor lenge spesialevnen varer

    while True:
        #Keybinds
        trykk = pygame.key.get_pressed()
        if trykk[pygame.K_SPACE] and pa_bakken:  #Sjekker om spilleren er i luften og kan hoppe
            figur_fart_y = -HOPPEKRAFT  #Starter hoppet
            pa_bakken = False  #Spilleren er ikke lenger på bakken

        for hendelse in pygame.event.get():
            if hendelse.type == pygame.QUIT:  #Lukker spillet hvis du klikker kryss
                pygame.quit()
                sys.exit()
            if hendelse.type == pygame.KEYDOWN:
                if hendelse.key == pygame.K_e and kjolenedteller_e == 0:  #Aktiverer E-evnen
                    evne_aktiv = True
                    evne_teller = EVNE_VARIGHET
                    kjolenedteller_e = COOLDOWN_E
                if hendelse.key == pygame.K_q and kjolenedteller_q == 0:  #Skyter et prosjektil
                    prosjektiler.append(Prosjektil(figur_rekt.centerx, figur_rekt.centery - 10, siste_retning))
                    kjolenedteller_q = COOLDOWN_Q

        #Bevegelse
        if trykk[pygame.K_a]:  #Bevegelse til venstre
            figur_rekt.x -= figur_fart_x
            siste_retning = -1
        if trykk[pygame.K_d]:  #Bevegelse til høyre
            figur_rekt.x += figur_fart_x
            siste_retning = 1

        #Tyngdekraft og bakken
        if not pa_bakken:  #Hvis spilleren er i lufta
            figur_fart_y += GRAVITASJON
        figur_rekt.y += figur_fart_y  #Flytt spilleren nedover
        if figur_rekt.colliderect(bakke_rekt):  #Sjekk om spilleren treffer bakken
            figur_rekt.y = bakke_rekt.top - figur_rekt.height
            pa_bakken = True
            figur_fart_y = 0
        else:
            pa_bakken = False

        #Oppdater fiender
        for fiende in fiender[:]:
            fiende.oppdater()  #Beveger fienden
            if evne_aktiv:  #Sjekker om spesialevnen er aktiv
                avstand = ((figur_rekt.centerx - fiende.rekt.centerx) ** 2 +
                           (figur_rekt.centery - fiende.rekt.centery) ** 2) ** 0.5
                if avstand <= SKADE_RADIUS:  #Skader fiender innen radius
                    fiende.ta_skade(50)
                    if fiende.helse <= 0:
                        fiender.remove(fiende)
                        poeng += 1  #Gir poeng for å fjerne en fiende
            if figur_rekt.colliderect(fiende.rekt):  #Sjekker kollisjon mellom figur og fiende
                spiller_helse -= 10
                if spiller_helse <= 0:  #Hvis helse når null, avslutt spillet
                    print("Spillet er over")
                    pygame.quit()
                    sys.exit()

        #prosjektiler
        for prosjektil in prosjektiler[:]:
            prosjektil.oppdater()  #flytter prosjektilene
            for fiende in fiender[:]:
                if prosjektil.rekt.colliderect(fiende.rekt):  #Sjekker treff på fiender
                    fiender.remove(fiende)
                    poeng += 1
            if prosjektil.rekt.left > BREDDE or prosjektil.rekt.right < 0:  #Fjerner prosjektiler som går utenfor skjermen
                prosjektiler.remove(prosjektil)

        #abilities/evner og cooldowns
        if evne_aktiv:
            evne_teller -= 1
            if evne_teller <= 0:
                evne_aktiv = False
        if kjolenedteller_e > 0:
            kjolenedteller_e -= 1
        if kjolenedteller_q > 0:
            kjolenedteller_q -= 1

        #nivå/level
        niva_teller += 1
        if niva_teller >= NIVA_VARIGHET:
            niva_teller = 0
            niva += 1
            for _ in range(niva):  #Legg til flere fiender
                fiender.append(spawn_fiende_trygt(figur_rekt.x, figur_rekt.y))

        #Flere fiender
        fiende_spawn_teller += 1
        if fiende_spawn_teller >= max(FIENDE_SPAWN_INTERVALL // niva, 20):
            fiende_spawn_teller = 0
            fiender.append(spawn_fiende_trygt(figur_rekt.x, figur_rekt.y))

        #Tegning
        skjerm.fill((135, 206, 235))  #Bakgrunnsfargen (lys blå)
        pygame.draw.rect(skjerm, (0, 255, 0), bakke_rekt)  #Tegner bakken
        skjerm.blit(figur_bilde, figur_rekt)  #Tegner figuren
        for fiende in fiender:
            fiende.tegn()
        for prosjektil in prosjektiler:
            prosjektil.tegn()
        vis_ui(poeng, kjolenedteller_e, kjolenedteller_q, niva)  #Oppdaterer UI

        #helsebar
        pygame.draw.rect(skjerm, (255, 0, 0), (10, 170, 200, 20))  #Rød bakgrunn for helsebaren
        pygame.draw.rect(skjerm, (0, 255, 0), (10, 170, 200 * (spiller_helse / 100), 20))  #Grønn del som viser gjenværende helse
        if evne_aktiv:
            pygame.draw.circle(skjerm, (255, 255, 0), figur_rekt.center, SKADE_RADIUS, 1)  #Tegner en sirkel for E-evnen

        pygame.display.flip()  #Oppdaterer skjermen
        klokke.tick(FPS)  #Holder spillet i riktig hastighet

if __name__ == "__main__":
    hoved()
