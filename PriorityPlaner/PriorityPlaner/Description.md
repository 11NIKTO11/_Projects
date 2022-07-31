Cieľom je naprogramovať prioritný plánovač.

### VSTUP :

txt file v určenom formáte, kde budú popísané aktivity, ich priorita/hodnota, pripustne časy vykonávania a potrebná dĺžka vykonávania.

### VÝSTUP: 

najlepší prípustný harmonogram aktivity zostrojitelny zo vstupu. tiež ako txt alebo na cout.

#### Obmedzenia:

- Plánovanie je na obdobie jedného dňa.
- Časy budu s presnosťou na minuty.  
- priority sa musia zmestiť do int

#### Rozšírenia:

- Rozdelenie času pri aktivite, aktivita nemusí byť vykonávaná vkuse, len určitý čas dohromady a s tým aj obmedzenia Min Max na dlšku neprerušovaného vykonávania 
- Plánovanie na dlhšie obdobie týždeň/mesiac
- Co-plánovanie aktivít pre viac osôb
- Rôzne priority pre rôzne časy pre jednu aktivitu
- Zahrnúť cestovanie do plánovania : na vstupe bude popis grafu miest a vzdialenosti 
- Možnosť pridávať reštrikcie Napr: nechcem aby sa vykonávali tieto dve aktivity posebe, a pod.
- Možnosť rozdelenia aktivít na kategórie a možnosť obmedziť počet alebo čas pre danu kategoriu