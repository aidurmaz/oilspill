#!/usr/bin/env python
#-*-coding:utf-8-*-

import psycopg2
from datetime import datetime
startTime = datetime.now()

baglanti_text="dbname=A_petrol"+" "+"user=postgres"+" "+"password=postgres"+" "+"port=5432"
table='petrol_demo'
conn = psycopg2.connect(baglanti_text)
db = conn.cursor()

sorgu='SELECT count(*) FROM {0};'.format(table)
db.execute(sorgu)
conn.commit()
kac_oge_var=(db.fetchall()[0][0])


def islmid_bul(conn, db,table):
    sorgu='SELECT * FROM %s where (hesap is null) or hesap=0 order by gid asc limit 1'%(table)
    db.execute(sorgu)
    conn.commit()
    sonuc=db.fetchall()
    islem_id=sonuc[0][0]
    yukseklik=sonuc[0][1]
    hacim=float(sonuc[0][5])
    baslangic=islem_id

    sorgu='update {0} set islem=0;'.format(table)
    db.execute(sorgu)
    conn.commit()
    
    return islem_id,baslangic,yukseklik,hacim


def math_hesap(conn, db,table,id,hacim):
    sorgu='update {0} set hesap={1} where gid={2};'.format(table,str(hacim),str(id))
    db.execute(sorgu)
    conn.commit()

##db.execute('SELECT * FROM %s order by gid asc limit 1'%(table))
##islem_id=db.fetchall()[0][0]
islem_id,baslangic,bas_yukseklik,bas_hacim=islmid_bul(conn, db,table)




def komsuluk(conn,db,id,table):
    id=str(id)
    sorgu=('WITH variables (var1) as (values ('+id+'))'+' select {0}.* from {0},variables where '+ 
        'ST_Touches({0}.geom,(SELECT {0}.geom FROM {0},variables WHERE {0}.gid = variables.var1)) and '+
        'parca=(select {0}.parca from {0},variables where {0}.gid=variables.var1) and '+
        'islem=0 LIMIT 1;').format(table)
    #print sorgu
    db.execute(sorgu)
    conn.commit()
    sonuc_var=db.rowcount
    if (sonuc_var==1):
        result_srg=db.fetchall()
        bulunanid=result_srg[0][0]
        yukseklik=int(result_srg[0][1])
        hacim=float(result_srg[0][5])
    sorgu=('UPDATE {0} SET islem = 1 where gid='+id+';').format(table)
    #print sorgu
    db.execute(sorgu)
    conn.commit()
    if (sonuc_var==1):
        return [bulunanid,yukseklik,hacim]
    else:
        return [-1,0,0]

ikinci=0
kactane=kac_oge_var
math_toplam_hacim=0
yukseklk_maks=bas_yukseklik
while True:
    
    if islem_id==-1:#dondugu yer
        islem_id=baslangic
        yukseklik=bas_yukseklik
        yukseklk_maks=bas_yukseklik
        ikinci=ikinci+1
    if ikinci==2:
        if baslangic==165:
            print str((bas_hacim)/2)+"--"+"yarim kalan"
            print "bakilan="+str(math_toplam_hacim+(bas_hacim)/2)
        math_toplam_hacim=math_toplam_hacim+(bas_hacim)/2
        if math_toplam_hacim==0:
             math_toplam_hacim=0.001
        math_hesap(conn, db,table,islem_id,math_toplam_hacim)
        if baslangic==kac_oge_var:
            break
        math_toplam_hacim=0
        islem_id,baslangic,bas_yukseklik,bas_hacim=islmid_bul(conn, db,table)
        ikinci=0
        yukseklik=bas_yukseklik
        yukseklk_maks=bas_yukseklik

        f = open("result.txt", "w")
        f.write(str(baslangic))
        f.close()        
    sonuc=komsuluk(conn,db,islem_id,table)
    islem_id=sonuc[0]
    yukseklik=sonuc[1]
    hacim=sonuc[2]
    if yukseklik>=yukseklk_maks:
        yukseklk_maks=yukseklik
        math_toplam_hacim=math_toplam_hacim+hacim
        if baslangic==165:
            print str(hacim)+"--"+str(math_toplam_hacim)
        
        
    

db.close()
print datetime.now() - startTime 