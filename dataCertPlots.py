import ROOT
import sys
import math
import numpy
import argparse


parser = argparse.ArgumentParser(description='Make data certifcation plots')
parser.add_argument('-c', '--certfile', type=str, default="", help='The data certfication tree')
parser.add_argument('-r', '--runlist', type=str, default="", help="Minimum fill number")
parser.add_argument('-o', '--outDir',  type=str, default="", help="Path to output directory")
parser.add_argument('-a', '--autogen', action='store_true', default=False, help="Auto generator list of runs from file")
parser.add_argument('-b', '--batch',   action='store_true', default=False, help="Batch mode (doesn't make GUI TCanvases)")
parser.add_argument('--csv', type=str, default="", help='The csv file of correction')
parser.add_argument('-d', '--docorr', action='store_true', default=False, help="do PCC aftergolw correction")

args = parser.parse_args()

ROOT.gStyle.SetPadTickY(2)

pcc_dict={}

miss_LS = []


if args.csv!="":
    file = open(args.csv)
    lines = file.readlines()
    for line in lines:
        items = line.split(",")
        fill = int(items[0])

        pcc_dict[fill]=float(items[1])
        print float(items[1])
   
print pcc_dict
rebinLS=1
scale=1
PCCscale=1
def ReStyleHistogram(hist,nRows=3):
    hist.GetXaxis().SetTitleSize(0.15*nRows/5)
    hist.GetXaxis().SetTitleOffset(-0.4)
    #hist.GetXaxis().SetNdivisions(1009)
    hist.SetLabelSize(0.14*nRows/5)
    hist.GetYaxis().SetTitleSize(0.12*nRows/5)
    hist.GetYaxis().SetTitleOffset(0.4)
    hist.SetMinimum(0.00001)
    hist.SetLineWidth(scale)


def GetMaximum(histList,scale=1.0):

    listMax=0
    for hist in histList:
        listMax=max(listMax,hist.GetMaximum())

    return listMax*scale


def GetYAverage(hist,zeroSupress=True):
    try:
        binsToAve=[]
        for ibin in range(1,hist.GetNbinsX()+1):
            if hist.GetBinContent(ibin)>0:
                binsToAve.append(hist.GetBinContent(ibin))

        mean=numpy.mean(binsToAve)
        std=numpy.std(binsToAve)
        meanError=std/math.sqrt(len(binsToAve))
        return mean,meanError

    except:
        print "Failed to get the average for",hist.GetName()
        return -999,-999


if args.batch is True:
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    scale=4

if args.outDir!="":
    if args.outDir[-1]!="/":
        args.outDir=args.outDir+"/"

filename=args.certfile
tfile=ROOT.TFile(filename)
tree=tfile.Get("certtree")

runsToCheck=[]
missingRuns=[]


if args.autogen:
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("run",1)
    nentries=tree.GetEntries()
    for ient in range(nentries):
        tree.GetEntry(ient)
        if tree.run not in runsToCheck:
            runsToCheck.append(int(tree.run))
            missingRuns.append(int(tree.run))
        
else:
    for run in args.runlist.split(","):
        runsToCheck.append(int(run))
        missingRuns.append(int(run))

runsToCheck.sort()
missingRuns.sort()
print runsToCheck
#246908,246919,246920,246923,246926,246930,246936,246951,246960,247068,247070,247073,247078,247079,247081,247252,247253,247262,247267,247377,247381

tree.SetBranchStatus("*",0)
tree.SetBranchStatus("fill",1)
tree.SetBranchStatus("run",1)
tree.SetBranchStatus("LS",1)
tree.SetBranchStatus("hasBrilData",1)
tree.SetBranchStatus("hasCMSData",1)
tree.SetBranchStatus("nActiveBX",1)

onlyBril=[]
onlyCMS=[]
bothSets=[]

runLSMax={}

nentries=tree.GetEntries()
for ient in range(nentries):
    tree.GetEntry(ient)
    if tree.run in missingRuns:
        missingRuns.remove(tree.run)
    if not runLSMax.has_key(tree.run):
        runLSMax[tree.run]=tree.LS
    elif runLSMax[tree.run]<tree.LS:
        runLSMax[tree.run]=tree.LS

    if tree.hasBrilData and tree.hasCMSData:
        bothSets.append(tree.run)
    elif tree.hasBrilData:
        onlyBril.append(tree.run)
    elif tree.hasCMSData:
        onlyCMS.append(tree.run)

print "missingRuns runs: ",missingRuns
print "Not both CMS and Bril: ",list(set(runsToCheck)-set(bothSets))


tree.SetBranchStatus("*",1)
histpix={}
histpix_HF = {}
histpix_BCMF = {}
histpix_PLT = {}
histPCLumiB3p8={}
histbest={}
histHFLumi={}
histBCMFLumi={}
histPLTLumi={}
histlayers={}
PCClayers={}
eventRate={}
layerColors=[616,1,632,600,416]
histPU={}
nActiveBX={}

bestHF={}
bestBCM1f={}
bestPLT={}

nBins={}
for run in runLSMax:
    bins=int(runLSMax[run]/rebinLS)+1
    runLSMax[run]=bins*rebinLS
    nBins[run]=bins

#yLabelPix="PCC/BestLumi*2^18*N_{BX}"
yLabelPix="Pixel Cluster xsec (ub)"

for ient in range(nentries):
    tree.GetEntry(ient)

    if not nActiveBX.has_key(tree.run):
        nActiveBX[tree.run] = tree.nActiveBX

    pcc_corr=0.8624
    if args.docorr:
        if pcc_dict.has_key(tree.fill):
            pcc_corr=pcc_dict[tree.fill]
    if tree.hasCMSData:
	
        if not eventRate.has_key(tree.run):
            eventRate[tree.run]=ROOT.TH1F(str(tree.run)+"_eventrate",";Luminosity Section  ;Event Rate (Hz)",nBins[tree.run],0,runLSMax[tree.run])
        eventRate[tree.run].Fill(tree.LS,tree.eventRate)
	
        if tree.nCluster>0:
            for layer in range(0,5):
                layerkey=str(tree.run)+"_PCClayer"+str(layer+1)
                if not PCClayers.has_key(layerkey):
                    PCClayers[layerkey]=ROOT.TH1F(str(tree.run)+"_PCClayer"+str(layer+1),";Luminosity Section  ;PCC Ratios in "+str(tree.run),nBins[tree.run],0,runLSMax[tree.run])
                    PCClayers[layerkey].SetLineColor(layerColors[layer])
                    ReStyleHistogram(PCClayers[layerkey],2)
                PCClayers[str(tree.run)+"_PCClayer"+str(layer+1)].Fill(tree.LS,tree.nPCPerLayer[layer]/tree.nCluster)
        else:
            print "For run,LS",tree.run,tree.LS,"nCluster is",tree.nCluster

    if tree.run in bothSets:
        if not histpix.has_key(tree.run):
            histpix[tree.run]=ROOT.TH1F(str(tree.run)+"pix",";Luminosity Section  ;"+yLabelPix,nBins[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix[tree.run],4)

            histpix_HF[tree.run]=ROOT.TH1F(str(tree.run)+"pixHF", ";Luminosity Section  ;"+yLabelPix, nBins[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_HF[tree.run],4)
            histpix_BCMF[tree.run]=ROOT.TH1F(str(tree.run)+"pixBCMF", ";Luminosity Section  ;"+yLabelPix, nBins[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_BCMF[tree.run],4)
            histpix_PLT[tree.run]=ROOT.TH1F(str(tree.run)+"pixPLT", ";Luminosity Section  ;"+yLabelPix, nBins[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histpix_PLT[tree.run],4)

            for layer in range(0,5):
                layerkey=str(tree.run)+"_layer"+str(layer+1)
                histlayers[layerkey]=ROOT.TH1F(str(tree.run)+"_layer"+str(layer+1),";Luminosity Section  ;"+yLabelPix,nBins[tree.run],0,runLSMax[tree.run])
                ReStyleHistogram(histlayers[layerkey],3)

        histpix[tree.run].Fill(tree.LS,tree.PC_xsec*PCCscale*pcc_corr)
        if (tree.HFLumi != 0):
            histpix_HF[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi*PCCscale*pcc_corr/tree.HFLumi)

        if (tree.PLTLumi != 0):
            histpix_PLT[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi*PCCscale*pcc_corr/tree.PLTLumi)

        if (tree.BCMFLumi != 0):
            histpix_BCMF[tree.run].Fill(tree.LS,tree.PC_xsec*tree.BestLumi*PCCscale*pcc_corr/tree.BCMFLumi)

        for layer in range(0,5):
            histlayers[str(tree.run)+"_layer"+str(layer+1)].Fill(tree.LS,tree.PC_xsec_layers[layer]*PCCscale*pcc_corr)

    if tree.BestLumi<=0 and tree.HFLumi<=0 and tree.BCMFLumi<=0 and tree.PLTLumi<=0 and tree.PC_lumi_B3p8>0:
        miss_LS.append([str(tree.run), str(tree.LS)])

    if tree.hasBrilData:
        key=tree.run
        if not histbest.has_key(key):
            histPCLumiB3p8[key]=ROOT.TH1F(str(tree.run)+"PCLumiB3p8",";Luminosity Section  ;Inst. Luminosity(Hz/#mub)",nBins[tree.run],0,runLSMax[tree.run])
            histbest[key]=ROOT.TH1F(str(tree.run)+"best",";Luminosity Section  ;Inst. Luminosity(Hz/#mub)",nBins[tree.run],0,runLSMax[tree.run])
            histHFLumi[key]=ROOT.TH1F(str(tree.run)+"HF",";Luminosity Section  ;Inst. Luminosity(Hz/#mub)",nBins[tree.run],0,runLSMax[tree.run])
            histBCMFLumi[key]=ROOT.TH1F(str(tree.run)+"BCMF",";Luminosity Section  ;Inst. Luminosity(Hz/#mub)",nBins[tree.run],0,runLSMax[tree.run])
            histPLTLumi[key]=ROOT.TH1F(str(tree.run)+"PLT",";Luminosity Section  ;Inst. Luminosity(Hz/#mub)",nBins[tree.run],0,runLSMax[tree.run])
            histPU[key]=ROOT.TH1F(str(tree.run)+"bestPU",";Luminosity Section  ;Pile-up",nBins[tree.run],0,runLSMax[tree.run])
            ReStyleHistogram(histbest[key],3)
            ReStyleHistogram(histPCLumiB3p8[key],3)
            ReStyleHistogram(histHFLumi[key],3)
            ReStyleHistogram(histBCMFLumi[key],3)
            ReStyleHistogram(histPLTLumi[key],3)
            ReStyleHistogram(histPU[key],3)
        if tree.BestLumi>0:#This is where it is fed in
            histbest[key].Fill(tree.LS,tree.BestLumi)
            histHFLumi[key].Fill(tree.LS,tree.HFLumi)
            histBCMFLumi[key].Fill(tree.LS,tree.BCMFLumi)
            histPLTLumi[key].Fill(tree.LS,tree.PLTLumi)
            if tree.hasCMSData:
                histPCLumiB3p8[key].Fill(tree.LS,tree.PC_lumi_B3p8*PCCscale*pcc_corr)
        if tree.BestLumi_PU>0:
            histPU[key].Fill(tree.LS,tree.BestLumi_PU*PCCscale*pcc_corr)
            #print tree.BestLumi_PU
        if tree.HFLumi>0 and tree.BCMFLumi>0 and tree.BestLumi>0:
            # FIXME USE ACTUAL BEST LUMI STRING FROM TREE (NOT IN TREE YET)
            if tree.run not in bestHF.keys():
                bestHF[tree.run]=0
                bestBCM1f[tree.run]=0
                bestPLT[tree.run]=0
            
            diffBestHF=math.fabs(tree.HFLumi-tree.BestLumi)
            diffBestBCMF=math.fabs(tree.BCMFLumi-tree.BestLumi)
            diffBestPLT=math.fabs(tree.PLTLumi-tree.BestLumi)
            minLumi=min(diffBestHF,min(diffBestBCMF,diffBestPLT))
            if minLumi==diffBestHF:
                bestHF[tree.run]=bestHF[tree.run]+1
            elif minLumi==diffBestBCMF:
                bestBCM1f[tree.run]=bestBCM1f[tree.run]+1
            elif minLumi==diffBestPLT:
                bestPLT[tree.run]=bestPLT[tree.run]+1
	

tcan=ROOT.TCanvas("tcan","",1200*scale,700*scale)
padlumis =ROOT.TPad("padlumis", "",0.0,0.0,0.5,1.0)
pad2 =ROOT.TPad("pad2","",0.5,0.0,1.0,1.0)

padlumis.Draw()
pad2.Draw()

PC_calib_xsec_B0=9.4e6
PC_calib_xsec_B3p8=9.4e6

for run in runsToCheck:

    padlumis.Divide(1,3)
    pad2.Divide(1,3)
    #pad2.Divide(1,4)
    lineB0=ROOT.TLine(0,PC_calib_xsec_B0,runLSMax[run],PC_calib_xsec_B0)
    lineB0.SetLineColor(634)
    lineB0.SetLineStyle(ROOT.kDashed)
    lineB0.SetLineWidth(2*scale)
    
    lineB3p8=ROOT.TLine(0,PC_calib_xsec_B3p8,runLSMax[run],PC_calib_xsec_B3p8)
    lineB3p8.SetLineColor(418)
    lineB3p8.SetLineStyle(ROOT.kDashed)
    lineB3p8.SetLineWidth(2*scale)

    legPixXSec=ROOT.TLegend(0.8,0.7,0.9,0.9)
    legPixXSec.AddEntry(lineB3p8,"B=3.8","l")
    legPixXSec.AddEntry(lineB0,"B=0","l")

    if run in histpix.keys():
        pixhistmax=histpix[run].GetMaximum()*1.4
        if pixhistmax>PC_calib_xsec_B3p8*1.5 or pixhistmax<PC_calib_xsec_B3p8:
            pixhistmax=PC_calib_xsec_B3p8*1.5

        pad2.cd(1)
        histpix[run].SetMaximum(pixhistmax)
        label=ROOT.TText(0,histpix[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section - Run="+str(run))
        label.SetTextSize(.1)
        histpix[run].Draw("hist")
        label.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        legPixXSec.Draw("same")
        pad2.Update()

        pad2.cd(2)
        eventRate[run].SetLineWidth(2)
        meanRate,meanRateError=GetYAverage(eventRate[run],True)
        ReStyleHistogram(eventRate[run],3)
        eventRate[run].Draw("hist")
        labelRate=ROOT.TText(0,eventRate[run].GetMaximum()*0.4,"      Average Rate in Run="+str(run)+" = "+"{0:.1f}".format(meanRate)+" Hz")
        labelRate.SetTextSize(.1)
        labelRate.Draw("same")
	
        pad2.Update()


#	pad2.cd(3)
#	#add my code right here.
#       histpix_HF[run].SetMaximum(pixhistmax)
	#set the maximum
#        label3=ROOT.TText(0,histpix_HF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section HF - Run="+str(run))
#        label3.SetTextSize(.1)
#        histpix_HF[run].Draw("hist")
#        label3.Draw("same")
#        lineB0.Draw("same")
#        lineB3p8.Draw("same")
#        legPixXSec.Draw("same")
#        histpix_BCMF[run].SetMaximum(pixhistmax)
#        label4=ROOT.TText(0,histpix_BCMF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section BCM1f - Run="+str(run))
#        label4.SetTextSize(.1)
#        histpix_BCMF[run].Draw("hist")
#        label4.Draw("same")
#        lineB0.Draw("same")
#        lineB3p8.Draw("same")
#        legPixXSec.Draw("same")
#	pad2.Update()

        #pad2.cd(3)
        #histpix_HF[run].SetMaximum(pixhistmax)
        #label3=ROOT.TText(0,histpix_HF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section HF - Run="+str(run))
        #label3.SetTextSize(.1)
        #histpix_HF[run].Draw("hist")
        #label3.Draw("same")
        #lineB0.Draw("same")
        #lineB3p8.Draw("same")
        #legPixXSec.Draw("same")
        #histpix_BCMF[run].SetMaximum(pixhistmax)
        #label4=ROOT.TText(0,histpix_BCMF[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section BCM1f - Run="+str(run))
        #label4.SetTextSize(.1)
        #histpix_BCMF[run].Draw("hist")
        #label4.Draw("same")
        #lineB0.Draw("same")
        #lineB3p8.Draw("same")
        #legPixXSec.Draw("same")
        #pad2.Update()

        #pad2.cd(4)
        #histpix_PLT[run].SetMaximum(pixhistmax)
        #label5=ROOT.TText(0,histpix_PLT[run].GetMaximum()*0.88,"   Pixel Cluster Cross Section PLT - Run="+str(run))
        #label5.SetTextSize(.1)
        #histpix_PLT[run].Draw("hist")
        #label5.Draw("same")
        #lineB0.Draw("same")
        #lineB3p8.Draw("same")
        #legPixXSec.Draw("same")
        #pad2.Update()
 
    if run in histbest.keys():
        padlumis.cd(1)
        maxHist=GetMaximum([histbest[run],histHFLumi[run],histBCMFLumi[run],histPLTLumi[run],histPCLumiB3p8[run]],1.1)

        if maxHist>2*histbest[run].GetMaximum():
            print "There is a serious outlier; setting max to 1.5*bestmax."
            maxHist=histbest[run].GetMaximum()*1.5


        histbest[run].SetLineColor(ROOT.kBlack)
        histbest[run].SetLineWidth(2*scale)
        histbest[run].SetMinimum(0)
        histbest[run].SetMaximum(maxHist)
        histbest[run].Draw("hist")
        print "intL for best in run",run,"is",histbest[run].Integral()
        histHFLumi[run].SetLineColor(633)
        histHFLumi[run].Draw("histsame")
        histBCMFLumi[run].SetLineColor(417)
        histBCMFLumi[run].Draw("histsame")
        histPLTLumi[run].SetLineColor(601)
        histPLTLumi[run].Draw("histsame")
        histPCLumiB3p8[run].SetLineColor(802)
        histPCLumiB3p8[run].Draw("histsame")

        intLPCC=histPCLumiB3p8[run].Integral()*23.31*1.e-6
        intLHF=histHFLumi[run].Integral()*23.31*1.e-6
        intLBCM=histBCMFLumi[run].Integral()*23.31*1.e-6
        intLPLT=histPLTLumi[run].Integral()*23.31*1.e-6

        leg=ROOT.TLegend(0.1,0.1,0.7,0.4)
        tot=1
        try:
            tot=float(bestHF[run]+bestBCM1f[run]+bestPLT[run])
            leg.AddEntry(histbest[run],"Best Lumi","l")
            leg.AddEntry(histHFLumi[run],"HF: "+"{0:.1f}".format((bestHF[run]/tot)*100)+"%,        Integrated Lumi = "+"{:2.2f}".format(intLHF)+" pb^{-1}","l")
            leg.AddEntry(histBCMFLumi[run],"BCM1f: "+"{0:.1f}".format((bestBCM1f[run]/tot)*100)+"%, Integrated Lumi = "+"{:2.2f}".format(intLBCM)+" pb^{-1}","l")
            leg.AddEntry(histPLTLumi[run],"PLT: "+"{0:.1f}".format((bestPLT[run]/tot)*100)+"%,  Integrated Lumi = "+"{:2.2f}".format(intLPLT)+" pb^{-1}","l")
            leg.AddEntry(histPCLumiB3p8[run],"PCC - B=3.8,   Integrated Lumi = "+"{:2.2f}".format(intLPCC)+" pb^{-1}","l")

            leg.SetFillStyle(0)
            leg.SetBorderSize(0)
            leg.Draw("same")
        except:
            try:
                print "HF,BCM1f,PLT",
                print bestHF.has_key[run]
                print bestBCM1f.has_key[run]
                print bestPLT.has_key[run]
            except:
                print "failed to count best lumi"
        padlumis.Update()
##best
        padlumis.cd(2)
        BestOPCLumi=histbest[run].Clone("best_o_PCLumi")
        BestOPCLumi.Divide(histPCLumiB3p8[run])
        BestOPCLumi.SetMaximum(2.0)
        BestOPCLumi.SetTitle(";Luminosity Section  ;Ratios")
        BestOPCLumi.SetLineColor(802)
        mean1,meanError1=GetYAverage(BestOPCLumi,True)
##hf
        HFOPCLumi=histHFLumi[run].Clone("HF_o_PCLumi")
        HFOPCLumi.Divide(histPCLumiB3p8[run])
        HFOPCLumi.SetMaximum(2.0)
        HFOPCLumi.SetTitle(";Luminosity Section  ;HF/PCLumi")
        HFOPCLumi.SetLineColor(800)
        mean2,meanError2=GetYAverage(HFOPCLumi,True)
##BCM1F
        BCM1FOPCLumi=histBCMFLumi[run].Clone("BCM1F_o_PCLumi")
        BCM1FOPCLumi.Divide(histPCLumiB3p8[run])
        BCM1FOPCLumi.SetMaximum(2.0)
        BCM1FOPCLumi.SetTitle(";Luminosity Section  ;BCM1F/PCLumi")
        BCM1FOPCLumi.SetLineColor(617)
        mean3,meanError3=GetYAverage(BCM1FOPCLumi,True)
##PLT
        PLTOPCLumi=histPLTLumi[run].Clone("PLT_o_PCLumi")
        PLTOPCLumi.Divide(histPCLumiB3p8[run])
        PLTOPCLumi.SetMaximum(2.0)
        PLTOPCLumi.SetTitle(";Luminosity Section  ;PLT/PCLumi")
        mean4,meanError4=GetYAverage(PLTOPCLumi,True)
##HF
        hfOverPLT=histHFLumi[run].Clone("HF_o_PLT")
        hfOverPLT.Divide(histPLTLumi[run])
        hfOverPLT.SetMaximum(2.0)
        hfOverPLT.SetTitle(";Luminosity Section  ;HF/PLTLumi")
        mean5,meanError5=GetYAverage(hfOverPLT,True)
##BCM1F
        bcmfOverPLT=histBCMFLumi[run].Clone("BCM1F_o_PLT")
        bcmfOverPLT.Divide(histPLTLumi[run])
        bcmfOverPLT.SetMaximum(2.0)
        bcmfOverPLT.SetTitle(";Luminosity Section  ;BCM1F/PLTLumi")
        mean6,meanError6=GetYAverage(bcmfOverPLT,True)


        leg2=ROOT.TLegend(0.1,0.7,0.5,0.9)
        print mean1,meanError1
        leg2.AddEntry(BestOPCLumi, "Best/PCLumi       =   "+"{:10.4f}".format(mean1)+" #pm "+"{:10.4f}".format(meanError1),"l")
        leg2.AddEntry(HFOPCLumi,   "HF/PCLumi         =   "+"{:10.4f}".format(mean2)+" #pm "+"{:10.4f}".format(meanError2),"l")
        leg2.AddEntry(BCM1FOPCLumi,"BCM1F/PCLumi  =   "+"{:10.4f}".format(mean3)+" #pm "+"{:10.4f}".format(meanError3),"l")
        leg2.AddEntry(PLTOPCLumi,  "PLT/PCLumi        =   "+"{:10.4f}".format(mean4)+" #pm "+"{:10.4f}".format(meanError4),"l")
        leg2.AddEntry(hfOverPLT,   "HF/PLT               =   "+"{:10.4f}".format(mean5)+" #pm "+"{:10.4f}".format(meanError5),"l")
        leg2.AddEntry(bcmfOverPLT, "BCM1F/PLT        =   "+"{:10.4f}".format(mean6)+" #pm "+"{:10.4f}".format(meanError6),"l")
        BestOPCLumi.Draw("hist")
	#take these histograms
        HFOPCLumi.Draw("histsame")
        BCM1FOPCLumi.Draw("histsame")
        PLTOPCLumi.Draw("histsame")
        hfOverPLT.Draw("histsame")
        bcmfOverPLT.Draw("histsame")
        leg2.Draw("sames")
        padlumis.Update()

        if run in bothSets:
            pad2.cd(3)
            histPU[run].Draw("hist")
            pad2.Update()
#move this to the right
        
        #dictionary, linearity plots
	linPlots = {}
        #TProfile (const char *name, const char *title, Int_t nbinsx, const Double_t *xbins, Option_t *option="")
	linPlots["HFoverPCC"]=ROOT.TProfile("",";PCC Average SBIL Hz/ub  ;Online/PCC",50,0,8,0,2)
        linPlots["HFoverPCC"].SetMaximum(2.0)
        iGraph=0
	for iBin in range(HFOPCLumi.GetNbinsX()):   #divide lumi by number of active bunches in fill
            lumi = histPCLumiB3p8[run].GetBinContent(iBin)/nActiveBX[run]
            ratio = HFOPCLumi.GetBinContent(iBin)
            if(ratio>0.1 and ratio<5 and lumi>0.0): #x_val = pcc inst. lumi (see histogram)
                linPlots["HFoverPCC"].Fill(lumi,ratio,iGraph)
		print str(lumi)+"	"+str(ratio)
                iGraph = iGraph+1
        #add titles and stuff        
	padlumis.cd(3)
        linPlots["HFoverPCC"].SetLineColor(ROOT.kRed)
	linPlots["HFoverPCC"].SetLineWidth(50)
        ReStyleHistogram(linPlots["HFoverPCC"],3)
	linPlots["HFoverPCC"].Draw("PE")
        
        fun_hfoverpcc=ROOT.TF1("fun_hfoverpcc", "[0]+[1]*x", 0, 20)
        linPlots["HFoverPCC"].Fit(fun_hfoverpcc, "N")
        hf_p0 = fun_hfoverpcc.GetParameter(0)
        hf_e0 = fun_hfoverpcc.GetParError(0)
        hf_p1 = fun_hfoverpcc.GetParameter(1)
        hf_e1 = fun_hfoverpcc.GetParError(1)
        
	padlumis.Update()
        
        linPlots["PLToverPCC"]=ROOT.TProfile("",";Hz/ub  ;Online/PCC",50,0,8,0,2)
        linPlots["PLToverPCC"].SetMaximum(2.0)
        iGraph=0
        for iBin in range(HFOPCLumi.GetNbinsX()):   
            lumi = histPCLumiB3p8[run].GetBinContent(iBin)/nActiveBX[run]
            ratio = PLTOPCLumi.GetBinContent(iBin)
            if(ratio>0.1 and ratio<5 and lumi>0.0): 
                linPlots["PLToverPCC"].Fill(lumi,ratio,iGraph)
                iGraph = iGraph+1        
        padlumis.cd(3)
	linPlots["PLToverPCC"].SetLineColor(ROOT.kBlue)
	linPlots["PLToverPCC"].SetLineWidth(50)
        ReStyleHistogram(linPlots["PLToverPCC"],3)
        linPlots["PLToverPCC"].Draw("pe same")
        padlumis.Update()

        fun_pltoverpcc=ROOT.TF1("fun_pltoverpcc", "[0]+[1]*x", 0, 20)
        linPlots["PLToverPCC"].Fit(fun_pltoverpcc, "N")
        plt_p0 = fun_pltoverpcc.GetParameter(0)
        plt_e0 = fun_pltoverpcc.GetParError(0)
        plt_p1 = fun_pltoverpcc.GetParameter(1)
        plt_e1 = fun_pltoverpcc.GetParError(1)
         
        linPlots["BCM1FoverPCC"]=ROOT.TProfile("",";Hz/ub  ;Online/PCC",50,0,8,0,2)
        linPlots["BCM1FoverPCC"].SetMaximum(2.0)
        iGraph=0
        for iBin in range(HFOPCLumi.GetNbinsX()):   
            lumi = histPCLumiB3p8[run].GetBinContent(iBin)/nActiveBX[run]
            ratio = BCM1FOPCLumi.GetBinContent(iBin)
            if(ratio>0.1 and ratio<5 and lumi>0.0): 
                linPlots["BCM1FoverPCC"].Fill(lumi,ratio,iGraph)
                iGraph = iGraph+1       
        padlumis.cd(3)
	linPlots["BCM1FoverPCC"].SetLineColor(ROOT.kGreen)
	linPlots["BCM1FoverPCC"].SetLineWidth(50)
	ReStyleHistogram(linPlots["BCM1FoverPCC"],3)
        linPlots["BCM1FoverPCC"].Draw("pe same")
        padlumis.Update()
        fun_bcm1foverpcc=ROOT.TF1("fun_bcm1foverpcc", "[0]+[1]*x", 0, 20)
        linPlots["BCM1FoverPCC"].Fit(fun_bcm1foverpcc, "N")
        bcm1f_p0 = fun_bcm1foverpcc.GetParameter(0)
        bcm1f_e0 = fun_bcm1foverpcc.GetParError(0)
        bcm1f_p1 = fun_bcm1foverpcc.GetParameter(1)
        bcm1f_e1 = fun_bcm1foverpcc.GetParError(1)

        leg6=ROOT.TLegend(0.1,0.7,0.5,0.9)
        print mean1,meanError1
#       mean4,meanError4=GetYAverage(PLTOPCLumi,True)
	ratio_mean1, ratio_meanError1=GetYAverage(linPlots["HFoverPCC"],True)
	ratio_mean2, ratio_meanError2=GetYAverage(linPlots["PLToverPCC"],True)
	ratio_mean3, ratio_meanError3=GetYAverage(linPlots["BCM1FoverPCC"],True)
        leg6.AddEntry(linPlots["HFoverPCC"],   "HF/PCC    Linearity Fit:  "+"p0="+"{:10.4f}".format(hf_p0)+"#pm"+"{:4.4f}".format(hf_e0)+", p1="+"{:10.4f}".format(hf_p1)+"#pm"+"{:4.4f}".format(hf_e1),"l")
        leg6.AddEntry(linPlots["PLToverPCC"],  "PLT/PCC   Linearity Fit:  "+"p0="+"{:10.4f}".format(plt_p0)+"#pm"+"{:4.4f}".format(plt_e0)+", p1="+"{:10.4f}".format(plt_p1)+"#pm"+"{:4.4f}".format(plt_e1),"l")
        leg6.AddEntry(linPlots["BCM1FoverPCC"],"BCM1F/PCC Linearity Fit:  "+"p0="+"{:10.4f}".format(bcm1f_p0)+"#pm"+"{:4.4f}".format(bcm1f_e0)+", p1="+"{:10.4f}".format(bcm1f_p1)+"#pm"+"{:4.4f}".format(bcm1f_e1), "l")
        leg6.SetFillStyle(0)
        leg6.SetBorderSize(0)
	leg6.Draw("same")
	padlumis.Update()	

    tcan.Update()
    tcan.SaveAs(args.outDir+str(run)+".png")
	
    #raw_input()
    padlumis.Clear()
    pad2.Clear()
    tcan.Update()

    if run in bothSets:
        layertexts={}
        lines={}
        canlayers=ROOT.TCanvas("canlayers","",1200,700)
        canlayers.Divide(2,3)

        canlayers.cd(1)
        ReStyleHistogram(histpix[run],3)
        histpix[run].Draw("hist")
        label.Draw("same")
        lineB0.Draw("same")
        lineB3p8.Draw("same")
        layermax=PC_calib_xsec_B3p8*1.15
        for layer in range(5):
            key=str(run)+"_layer"+str(layer+1)
            if histlayers[key].GetMaximum()*1.15 > layermax:
                layermax=histlayers[key].GetMaximum()*1.15
        layermax=min(layermax,PC_calib_xsec_B3p8*1.5)
        for layer in range(5):
            lines[layer]=ROOT.TF1("pol1_"+str(layer+1),"pol1",70,175)
            canlayers.cd(layer+2)
            key=str(run)+"_layer"+str(layer+1)
            layertexts[layer]=ROOT.TText(0,layermax*1.05,"    Pixel Cluster Cross Section - Layer="+str(layer+1))
            layertexts[layer].SetTextSize(.1)
            histlayers[key].SetMaximum(layermax)
            histlayers[key].Draw("hist")
            layertexts[layer].Draw("same")
        canlayers.Update()
        canlayers.SaveAs(args.outDir+str(run)+"_layers.png")


    if run in bothSets or run in onlyCMS:
        layertexts={}
        lines={}
        stability=ROOT.TCanvas("stability","",1200,700)
        stabLeg=ROOT.TLegend(0.5,0.20,0.9,0.43)
    
        for layer in range(5):
    
            key=str(run)+"_PCClayer"+str(layer+1)
            mean,meanError=GetYAverage(PCClayers[key],True)
            print mean, meanError
            stabLeg.AddEntry(PCClayers[key],"Layer "+str(layer+1)+" / Layer 2-5   "+"{:10.4f}".format(mean)+" #pm "+"{:10.4f}".format(meanError),"l")
            if layer==0:
                PCClayers[key].Draw("hist")
                PCClayers[key].SetMinimum(0.18)
                PCClayers[key].GetYaxis().SetTitleOffset(0.7)
            else:
                PCClayers[key].Draw("histsame")
        stabLeg.Draw("same")
        stability.Update()
        stability.SaveAs(args.outDir+str(run)+"_stability.png")

print "Missing LSs: ",miss_LS
