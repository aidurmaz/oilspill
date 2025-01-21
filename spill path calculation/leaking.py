# -*- coding: utf-8 -*-
import arcpy
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = 1

#petrol sizintisinin baslangic noktasının arcpy ile değişken olarak alındığı satır
baslangic=arcpy.GetParameterAsText(0)
#dağılıma konu petrol hacminin arcpy ile tamimlandiği satir
petrol_miktari=float(arcpy.GetParameterAsText(1))
#çok yüksek yatay çözünürlüklü dem verilerinde çalışılmayı olanak sağlayan petrolün yatay çözünürlüğe göre yükselme oranı arpy ile tanımlanır ara yüzden gelir
hacim_orani=float(arcpy.GetParameterAsText(2))
#litoloji değeri gigip girmeyeceği bilgisi arayüzden kullanıcı tanımlar
litoloji_var_yok=arcpy.GetParameterAsText(3)
#litoloji tanımlanmamışsa sabir pixel bazlı emilim miktarı
pixel_emme=float(arcpy.GetParameterAsText(4))


mxd = arcpy.mapping.MapDocument("CURRENT")

pathmxd=(mxd.filePath).encode('utf8')
pathmxdlist=pathmxd.split("\\")
pathmxdlist.pop(len(pathmxdlist)-1)
pathmxd="\\".join(pathmxdlist)
workspace=pathmxd
arcpy.env.workspace=workspace

#kullanıcı tarafından girilen başlangıç noktasının shp olarak kayıt ediliyor
arcpy.FeatureClassToFeatureClass_conversion(baslangic,  workspace+r"\data\output", "baslangic.shp")

#başlanıgç noktasından dem yaztay çözünürlüğü göz önüne alınarak en fazla sızıntının olacağı bir bölgeden dem değeri kesiliyor ve bundan sonra işlemler bu dem verisi üzerinden yapılcak
arcpy.Buffer_analysis(baslangic,workspace+r"\data\output\kesme_buffer.shp","10 Kilometers","FULL","ROUND","ALL")
arcpy.gp.ExtractByMask_sa(workspace+r"\toolbox\tr_dem_wgs.tif", workspace+r"\data\output\kesme_buffer.shp",workspace+r"\data\output\kesme_raster.tif")
#raster formatta olan dem verisi komşulukanalizi gibi işelmer için vektör formata çevriliyor
arcpy.RasterToPolygon_conversion(workspace+r"\data\output\kesme_raster.tif", workspace+r"\data\output\calisma_alan.shp", "NO_SIMPLIFY","VALUE")


#vektör formata çevrilen dem verisine hesaplama işlemleri yapılabilmesi için alttaki yeni kolon yapıları ekleniyor
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "durum", "SHORT")
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "yukselme", "FLOAT")
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "alan", "FLOAT")
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "biriken", "FLOAT")
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "lito_emme", "FLOAT")
arcpy.AddField_management(workspace+r"\data\output\calisma_alan.shp", "sira", "SHORT")


#kullanıcı  litoloji değeri gösterip göstermemesine göre vektöre çevrilmiş dem litoloji katmanına göre parçalara ayrılıyor. litoloji gösterilmez ise dem değeri parçalanmıyor
if litoloji_var_yok=="Stabil Deger":
      arcpy.MakeFeatureLayer_management(workspace+r"\data\output\calisma_alan.shp", "dem_lyr")
else:
      arcpy.Intersect_analysis([workspace+r"\data\litoloji.shp",workspace+r"\data\output\calisma_alan.shp"], workspace+r"\data\output\calisma_alan2.shp", "", "" "")
      arcpy.MakeFeatureLayer_management(workspace+r"\data\output\calisma_alan2.shp", "dem_lyr")

#her bir pikselin alan değir hesaplanıyor bu değer birikme işlemlerinde kullanılacaktır
arcpy.CalculateField_management("dem_lyr", "alan",'!shape.area@SQUAREMETERS!', "PYTHON_9.3")


#başlangıç noktasındaki ilk sızıntının başlayacağı piksel intersection alanlizi ile bulunuyor      
arcpy.SelectLayerByLocation_management ("dem_lyr", "INTERSECT", baslangic,"","NEW_SELECTION")
f1 = "GRIDCODE"
liste_komsular=[]
for row in sorted(arcpy.da.SearchCursor("dem_lyr", [f1])):
      liste_komsular.append(row[0])
#min_yukselme değişkenine başlangıç noktasının yükseklik değeri atanıyor
min_yukselme=min(liste_komsular)

#başlangıç pikseline dokunan piksellerden yükseklik deperi en küşük olan tüm pikseller seçiliyor
arcpy.SelectLayerByLocation_management ("dem_lyr", "BOUNDARY_TOUCHES", "","","NEW_SELECTION")
experssion = '\"GRIDCODE\" ='+str(int(min(liste_komsular)))
arcpy.SelectLayerByAttribute_management ("dem_lyr", "SUBSET_SELECTION",experssion)


#seçilen piksllerde işlem yapıldığına dair 1 değeri atanıp yükselme değerine başlangıç pikselinin yükselik değeri yazılıyor
arcpy.CalculateField_management("dem_lyr", "durum",'1', "PYTHON_9.3")
arcpy.CalculateField_management("dem_lyr", "yukselme",'!GRIDCODE!', "PYTHON_9.3")


i=1
#toplam kayıp miktarı girilen sızıntı hacmine büyük eşit olana kadar düngüye giriliyor
while True:
      #işlem yapılan sızıntı güzergahı seçiliyor bu seçim üzerinde kayıp hacmi hesaplanacak
      arcpy.SelectLayerByAttribute_management ("dem_lyr", "NEW_SELECTION",'"durum"=1')

      #litoloji emilim ve birikmeden kaynaklı toplam kayıp hacmi hesaplanıyor
      if litoloji_var_yok=="Stabil Deger":
            arcpy.Statistics_analysis("dem_lyr", workspace+r"\toolbox\tablo.gdb\sonuc", [["biriken", "SUM"],["biriken","COUNT"]])
            f1,f2 = "SUM_biriken","COUNT_biriken"
            for row in arcpy.da.SearchCursor(workspace+r"\toolbox\tablo.gdb\sonuc", [f1, f2]):
                  pass
            
            deger=row[0]+pixel_emme*row[1]
      else:
            arcpy.Statistics_analysis("dem_lyr", workspace+r"\toolbox\tablo.gdb\sonuc", [["biriken", "SUM"],["lito_emme","SUM"]])
            f1,f2 = "SUM_biriken","SUM_lito_emme"
            for row in arcpy.da.SearchCursor(workspace+r"\toolbox\tablo.gdb\sonuc", [f1, f2]):
                  pass
            deger=row[0]+row[1]
            
      #eğer toplam kayıp sızıntı hacmine büyük eşit ise döngüden çıkılıyor
      if deger>=petrol_miktari:
            break


      #şu ana kadar işlem yapılmış tüm sızıntı güzergahı bulunuyor bu güzergaha komşu olan tüm pikseller seçiliyor
      arcpy.SelectLayerByLocation_management ("dem_lyr", "BOUNDARY_TOUCHES", "","","NEW_SELECTION")
      arcpy.SelectLayerByAttribute_management ("dem_lyr", "REMOVE_FROM_SELECTION",'"durum"=1')

      #mevcut sızıntı güzergahına komşu olan ve yükseklik değeri en küçük olan pikseller değeri tespit ediliyor
      f1 = "GRIDCODE"
      liste_komsular=[]
      for row in sorted(arcpy.da.SearchCursor("dem_lyr", [f1])):
            liste_komsular.append(row[0])

      min_yukselme=min(liste_komsular)
      experssion = '\"GRIDCODE\" ='+str(int(min(liste_komsular)))

      #komşu piksllerin içinde yüksekili en küçük olan tüm pikseller seçiliyor bu pikseller daha sonra işlem yapılan piksel olarak atanacaktır
      arcpy.SelectLayerByAttribute_management ("dem_lyr", "SUBSET_SELECTION",experssion)
      
      onceki_sayi = int(arcpy.GetCount_management("dem_lyr").getOutput(0)) 
      sonraki_sayi=onceki_sayi+1
      
      #en düşük yüksekliğe sahip komşu piksellerin etrafındaki piksellerde tespit edilen yükseklik değerine eşit veya bu değerden daha küçük yüksekli değeri varmı diye kotrol sağlanıyor
      while True:
            if onceki_sayi>=sonraki_sayi:
                  break
            onceki_sayi = int(arcpy.GetCount_management("dem_lyr").getOutput(0)) 
            
            arcpy.SelectLayerByLocation_management ("dem_lyr", "BOUNDARY_TOUCHES", "","","NEW_SELECTION")
            arcpy.SelectLayerByAttribute_management ("dem_lyr", "REMOVE_FROM_SELECTION",'"durum"=1')
            arcpy.SelectLayerByAttribute_management ("dem_lyr", "SUBSET_SELECTION",experssion)

            sonraki_sayi = int(arcpy.GetCount_management("dem_lyr").getOutput(0))

      #yeni belirlenen tüm piksller akıntı güzergahına eklenmektedir      
      arcpy.CalculateField_management("dem_lyr", "durum",'1', "PYTHON_9.3")
      #seçilen piksellere hangi sırada işlem yapıldığına dair sıra numarası veriliyor
      arcpy.CalculateField_management("dem_lyr", "sira",i, "PYTHON_9.3")

      #yeni bulunan minimum komşu piksel yüksekli değeri eğer en düşük olarak belirlenen yükseklik değerinden büyük piksel varsa bu piksellerde birikme olacağından tespit edilen güzergahtaki birikme hacmi hesaplanıyor
      experssion = '\"durum\"=1 AND \"yukselme\"<='+str(min_yukselme)
      arcpy.SelectLayerByAttribute_management ("dem_lyr", "NEW_SELECTION",experssion)
      arcpy.CalculateField_management("dem_lyr", "yukselme",min_yukselme, "PYTHON_9.3")
      experssion = "(!yukselme!-!GRIDCODE!)*!alan!"
      arcpy.CalculateField_management("dem_lyr", "biriken",experssion, "PYTHON_9.3")

      #eğer emilim değeri litoloji üzerinden geliyor ise piksellerdeki toplam emilim hesaplanıyor
      if litoloji_var_yok!="Stabil Deger":
            experssion = "!emme!"
            arcpy.CalculateField_management("dem_lyr", "lito_emme",experssion, "PYTHON_9.3")   
      i=i+1
      arcpy.AddMessage(i)
#topam kayıp miktarının sızıntı hacminden büyük eşit olduğu anda hesaplan sonuç bilgileri kayıt ediliyor      
arcpy.AddMessage(deger)
arcpy.SelectLayerByAttribute_management ("dem_lyr", "NEW_SELECTION",'"durum"=1')
arcpy.FeatureClassToFeatureClass_conversion("dem_lyr",  workspace+r"\data\output", "cikti.shp")
arcpy.AddField_management(workspace+r"\data\output\cikti.shp", "sonuc", "FLOAT")
arcpy.CalculateField_management(workspace+r"\data\output\cikti.shp", "sonuc",'!yukselme!-!GRIDCODE!', "PYTHON_9.3")

newlayer = arcpy.mapping.Layer(workspace+r"\data\output\cikti.shp")
df = mxd.activeDataFrame
arcpy.mapping.AddLayer(df, newlayer, "TOP")
mxd.save()