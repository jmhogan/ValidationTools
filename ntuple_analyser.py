#!/usr/bin/env python
from ROOT import TH1D, TFile, TLorentzVector, TProfile, TProfile2D, TVector2, TVector3
#from __future__ import print_function
from bin.NtupleDataFormat import Ntuple
import sys
import optparse
import itertools
import math
from array import array

# The purpose of this file is to demonstrate mainly the objects
# that are in the HGCalNtuple

pdgid = {
    "photon": 22,
    "electron": 11,
    "muon": 13,
    
}
def createHist(opt, varname, params):
    if "pt" in varname and "resolution" not in varname:
        h = TH1D(varname, "", 50, params["plotPtRange"][0], params["plotPtRange"][1])
        h.GetXaxis().SetTitle("p_{T} [GeV]")
        h.GetYaxis().SetTitle("N")
    elif "eta" in varname and "resolution" not in varname:
        h = TH1D(varname, "", 50, params["plotEtaRange"][0], params["plotEtaRange"][1])
        h.GetXaxis().SetTitle("#eta")
        h.GetYaxis().SetTitle("N")
    elif "phi" in varname:
        h = TH1D(varname, "", 50, params["plotPhiRange"][0], params["plotPhiRange"][1])
        h.GetXaxis().SetTitle("#phi")
        h.GetYaxis().SetTitle("N")
    elif "mass" in varname:
        h = TH1D(varname, "", 50, params["plotMassRange"][0], params["plotMassRange"][1])
        h.GetXaxis().SetTitle("mass [GeV]")
        h.GetYaxis().SetTitle("N")
    elif "idpass" in varname:
        h = TH1D(varname, "", 20, 0, 20)
        h.GetXaxis().SetTitle("ID bit value")
        h.GetYaxis().SetTitle("N")
    elif "isopass" in varname:
        h = TH1D(varname, "", 20, 0, 20)
        h.GetXaxis().SetTitle("isolation bit value")
        h.GetYaxis().SetTitle("N")

    elif "resolution" in varname:
        h = TH1D(varname, "", 100,params["plotResoRange"][0], params["plotResoRange"][1])
        h.GetXaxis().SetTitle("p_{T}^{reco} / p_{T}^{gen}")
        h.GetYaxis().SetTitle("N")

    elif "multi" in varname:
        if "full" in opt.outFile:
            h = TH1D(varname, "", params["plotNObjRange_Full"][1], params["plotNObjRange_Full"][0], params["plotNObjRange_Full"][1]) 
        else:
            h = TH1D(varname, "", params["plotNObjRange_Delp"][1], params["plotNObjRange_Delp"][0], params["plotNObjRange_Delp"][1])
        h.GetXaxis().SetTitle("multiplicity")
        h.GetYaxis().SetTitle("Events")

        
    h.Sumw2()

    return h

def create2dHist(varname, params, title):

    if "to_pt" in varname:
        h = TProfile(varname, title, 50, params["plotPtRange"][0], params["plotPtRange"][1])
        h.GetXaxis().SetTitle("gen p_{T} [GeV]")

        if "response" in varname:
            title = title.replace(")*#varepsilon(#","+")
            title = title.replace("#varepsilon","response")
            h.GetYaxis().SetTitle("Reco_pt/Gen_pt")
        elif 'efficiency' in varname:
            h.GetYaxis().SetTitle("gen object efficiency")
        elif 'nonprompt' in varname:
            h.GetYaxis().SetTitle("gen object nonprompt efficiency")
        elif 'fakerate' in varname:
            title = title.replace(")*#varepsilon(#","+")
            title = title.replace("#varepsilon","fakerate")
            h.GetXaxis().SetTitle("reco p_{T} [GeV]")
            h.GetYaxis().SetTitle("mistag rate")
    elif "to_eta" in varname:
        h = TProfile(varname, title, 50, params["plotEtaRange"][0], params["plotEtaRange"][1])
        h.GetXaxis().SetTitle("gen #eta [GeV]")

        if "response" in varname:
            title = title.replace(")*#varepsilon(#","+")
            title = title.replace("#varepsilon","response")
            h.GetYaxis().SetTitle("Reco_pt/Gen_pt")
        elif 'efficiency' in varname:
            h.GetYaxis().SetTitle("gen object efficiency")
        elif 'nonprompt' in varname:
            h.GetYaxis().SetTitle("gen object nonprompt efficiency")
        elif 'fakerate' in varname:
            title = title.replace(")*#varepsilon(#","+")
            title = title.replace("#varepsilon","fakerate")
            h.GetXaxis().SetTitle("reco #eta [GeV]")
            h.GetYaxis().SetTitle("mistag rate")

    h.Sumw2()

    return h

def create2Dmap(varname, params, title, dumptcl):
    
    ## use the slices to build a list of bin edges
    ptbins = [item[0] for item in params["ptSlices"]]
    etabins = [item[0] for item in params["etaSlices"]]
    ptbins.append(params["ptSlices"][-1][1])
    etabins.append(params["etaSlices"][-1][1])
    ## set more realistic caps
    if not dumptcl:
        if ptbins[-1] > 5e4: ptbins[-1] = ptbins[-2]*2. ## probably somewhere in 200 -- 4000?
        if etabins[-1] > 5e4: etabins[-1] = 5. 

    ptbinsext = []
    for iedge in range(0,len(ptbins)-1):
        #print "ptbins"+str(ptbins)
        binwidth = ptbins[iedge+1]-ptbins[iedge]
        if ptbins[iedge+1] >= 9e4: 
            ptbinsext.append(ptbins[iedge])
            continue # don't subdivide the overflow bin
        nsplits = params["sliceSplit"]
        if ptbins[iedge+1] >= 150 or ptbins[iedge] == 100:
            nsplits = 2
        for j in range(0,nsplits): # 0, 1, 2 if sliceSplit = 3
            ptbinsext.append(ptbins[iedge] + int(j*binwidth/nsplits)) # low, low+0*width/3, low+width/3, low+2*width/3
    ptbinsext.append(ptbins[-1])
    #print ptbinsext

    etabinsext = []
    for iedge in range(0,len(etabins)-1):
        #print "etabins"+str(etabins)
        binwidth = etabins[iedge+1]-etabins[iedge]
        if etabins[iedge+1] >= 9e4: 
            etabinsext.append(etabins[iedge])
            continue # don't subdivide the overflow bin
        nsplits = params ["sliceSplit"]
        if 'electron' in varname and etabins[iedge] == 1.5: nsplits = 7
        for j in range(0,nsplits): # 0, 1, 2 if sliceSplit = 3
            etabinsext.append(etabins[iedge] + j*binwidth/nsplits) # low, low+0*width/3, low+width/3, low+2*width/3
    etabinsext.append(etabins[-1])
    #print etabinsext

    ## arrays for ROOT
    xbins = array('d', ptbinsext)
    ybins = array('d', etabinsext)
    if "efficiency" in varname:
        h = TProfile2D(varname, title, len(xbins)-1, xbins, len(ybins)-1, ybins)
        h.GetXaxis().SetTitle("gen p_{T} [GeV]")
        h.GetYaxis().SetTitle("gen #eta")
    if "fake" in varname:
        title = title.replace(")*#varepsilon(#","+")
        title = title.replace("#varepsilon","fakerate")
        h = TProfile2D(varname, title, len(xbins)-1, xbins, len(ybins)-1, ybins)
        h.GetXaxis().SetTitle("reco p_{T} [GeV]")
        h.GetYaxis().SetTitle("reco #eta")
        
    h.Sumw2()
    return h

def findZ(genparts, ptCut, etaCut):
    v= TVector2(0, 0)
    for g in genparts:
        if abs(g.pid())==23: 
            d1 = g.d1()
            if d1<0: 
                continue
            gd1 = genparts[d1]
            if ( abs(gd1.pid())==11 or abs(gd1.pid()==13) ) and g.pt() > ptCut and abs(g.eta()) < etaCut :
                v.SetMagPhi(g.pt(),g.phi())
                return v
    return v

def findRecoZ(leptons, ptCut, etaCut, idCut, isoCut):
    if leptons[0].charge()*leptons[1].charge() > 0:
        return TVector3(0,0,0)
    v1= TVector3(0,0,0)
    v2= TVector3(0,0,0)
    if (leptons[0].pt() > ptCut and abs(leptons[0].eta()) <etaCut and leptons[0].idpass() > idCut and leptons[0].isopass() > isoCut  
        and leptons[1].pt() > ptCut and abs(leptons[1].eta()) <etaCut and leptons[1].idpass() > idCut and leptons[1].isopass() > isoCut) :
        v1.SetPtEtaPhi(leptons[0].pt(), leptons[0].eta(), leptons[0].phi())
        v2.SetPtEtaPhi(leptons[1].pt(), leptons[1].eta(), leptons[1].phi())
    return v1+v2
    

def doSum(objs, ptCut, etaCut):
    s = 0
    for j in objs:
        if j.pt()> ptCut and abs(j.eta())< etaCut :
            s += j.pt()
    return s

def doCount(objs, ptCut, etaCut):
    cnt = 0
    for j in objs:
        if j.pt()> ptCut and abs(j.eta())< etaCut :
            cnt += 1
    return cnt

def createMetHist(varname, xTitle, nBinsX, xMin, xMax):
    h = TH1D(varname, "", nBinsX, xMin, xMax)
    h.GetXaxis().SetTitle(xTitle)
    h.GetYaxis().SetTitle("Events")
    return h

def runMETStudy(ntuple, maxEvents, outfileName):

    tot_nevents = 0
    outputF = TFile(outfileName, "RECREATE")
    ## create histo
    metHists = {}
    metHists['genht_pt30_eta5'] = createMetHist('genht_pt30_eta5', "H_{T} gen [GeV]", 50, 0, 500)
    metHists['npuVtx'] = createMetHist('npuVtx', "npuVertices", 40, 100, 300)
    metHists['z_pt'] = createMetHist('z_pt', "p_{T}(Z) [GeV]", 40, 0, 150)
    metHists['genz_pt'] = createMetHist('genz_pt', "p_{T}(gen Z) [GeV]", 40, 0, 150)
    metHists['met'] = createMetHist('met', "p_{T,miss} [GeV]", 40, 0, 150)
    metHists['met_p'] = createMetHist('met_p', "parallel p_{T,miss} [GeV]", 40, 0, 150)
    metHists['met_t'] = createMetHist('met_t', "transverse p_{T,miss} [GeV]", 40, 0, 150)
    metHists['u_p'] = createMetHist('u_p', "u_{p} [GeV]", 40, 0, 150)
    metHists['u_t'] = createMetHist('u_t', "u_{t} [GeV]", 40, 0, 150)

    twodvarList=['genz_pt','genht_pt30_eta5','npuVtx']
    varList = ['z_pt', 'met', 'met_p', 'met_t', 'u_p', 'u_t']
    varAllList = varList +twodvarList
    for v in varList:
        for twodv in twodvarList:
            metHists[v+'_VS_'+twodv] = TProfile(v+'_VS_'+twodv, "", metHists[twodv].GetNbinsX(), metHists[twodv].GetXaxis().GetBinLowEdge(1), metHists[twodv].GetXaxis().GetBinUpEdge(metHists[twodv].GetNbinsX()))
            metHists[v+'_VS_'+twodv].GetXaxis().SetTitle(metHists[twodv].GetXaxis().GetTitle())
            metHists[v+'_VS_'+twodv].GetYaxis().SetTitle(metHists[v].GetXaxis().GetTitle())

    ## study
    for event in ntuple:
        if maxEvents > 0 and event.entry() >= maxEvents:
            break
        if (tot_nevents %1000) == 0 :
            print '... processed {} events ...'.format(event.entry()+1)

        tot_nevents += 1
        genparts = event.genparticles()
        genjets = event.genjets()
        mets = event.metspuppi()
        electrons = event.electrons()
        muons = event.muons()

        if len(electrons)>1: 
            leptons = electrons
        elif len(muons)>1: 
            leptons = muons
        else:
            continue

        z3d = findRecoZ(leptons, 15., 2., 0, 0) 
        z = TVector2(0,0)
        z.SetMagPhi(z3d.Pt(), z3d.Phi())
        z_pt = z.Mod()
        if not (z_pt>10.): continue
        genz = findZ(genparts, 15., 2.)
        genz_pt = genz.Mod()
        if not (genz_pt>10.): continue
        genht_pt30_eta5 = doSum(genjets, 30., 5.)
        met_v = TVector2(0,0)
        met_v.SetMagPhi(mets[0].pt(),mets[0].phi())
        met = mets[0].pt()
        met_p = met_v.Proj(z).Mod()
        met_t = met_v.Norm(z).Mod() 
        u_p = (z+met_v).Proj(z).Mod()
        u_t = (z+met_v).Norm(z).Mod()
        genjet_size_pt30_eta5 = doCount(genjets, 30., 5.)
        vtx_size = event.vtxSize()
        npuVtx = event.npuVertices()
        trueInt = event.trueInteractions()

        var = {}
        var['genht_pt30_eta5'] = genht_pt30_eta5
        var['npuVtx'] = npuVtx
        var['z_pt'] = z_pt
        var['genz_pt'] = genz_pt
        var['met'] = met
        var['met_p'] = met_p
        var['met_t'] = met_t
        var['u_p']= u_p
        var['u_t']= u_t

        for v in varAllList:
            metHists[v].Fill(var[v])

        for v in varList:
            for twodv in twodvarList:
                metHists[v+'_VS_'+twodv].Fill(var[twodv], var[v])
     
    ## write event level var hists
    outputF.cd()
    for h in metHists.keys():
        metHists[h].Write()

    for i in twodvarList:
        up_over_qt=outputF.Get("u_p_VS_"+i).Clone()
        up_over_qt.Divide(outputF.Get("z_pt_VS_"+i))
        up_over_qt.Write("up_over_qt_VS_"+i)

        ut=outputF.Get("met_t_VS_"+i).Clone()
        ut_rms= TH1D("ut_rms_VS_"+i, "", metHists[i].GetNbinsX(), 0, metHists[i].GetXaxis().GetBinUpEdge(metHists[i].GetNbinsX()))
        ut_rms.GetXaxis().SetTitle(metHists[i].GetXaxis().GetTitle())
        ut_rms.GetYaxis().SetTitle("RMS u_{T}")
        for imtt in range(1,ut.GetNbinsX()+1):
            ut_rms.SetBinContent(imtt, ut.GetBinError(imtt)*math.sqrt(ut.GetBinEntries(imtt)))
        ut_rms.Write()

        up_plus_qt =outputF.Get("met_p_VS_"+i).Clone()
        up_plus_qt_rms = TH1D("up_plus_qt_rms_VS_"+i, "", metHists[i].GetNbinsX(),0,metHists[i].GetXaxis().GetBinUpEdge(metHists[i].GetNbinsX()))
        up_plus_qt_rms.GetXaxis().SetTitle(metHists[i].GetXaxis().GetTitle())
        up_plus_qt_rms.GetYaxis().SetTitle("RMS u_{P}+q_{T}")
        for imtt in range(1,up_plus_qt.GetNbinsX()+1):
            up_plus_qt_rms.SetBinContent(imtt, up_plus_qt.GetBinError(imtt)*math.sqrt(up_plus_qt.GetBinEntries(imtt)))
        up_plus_qt_rms.Write()

    outputF.Close()

def main():

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-i', '--inFile',
                      dest='inFile',
                      help='input file [%default]',  
                      default=None,                                                                                                           
                      type='string')
    parser.add_option('-o', '--outFile',          
                      dest='outFile',       
                      help='output file [%default]',  
                      default='histo_delp/val.root',       
                      type='string')
    parser.add_option('-p', '--physObj',          
                      dest='physobject',       
                      help='object to analyze [%default]',
                      default='jet',
                      type='string')
    parser.add_option('--maxEvents',          
                      dest='maxEvts',
                      help='max number of events [%default]',
                      default=500000,
                      type=int)
    parser.add_option('--dumptcl',
                      dest='dumptcl',
                      help='use more bins for making tcl file?',
                      action="store_true",
                      default=False)
    (opt, args) = parser.parse_args()


    inFile = opt.inFile
    print 'READING: ',inFile
    ntuple = Ntuple(inFile)
    maxEvents = opt.maxEvts
    dumptcl = opt.dumptcl

    if opt.physobject == "met":
        runMETStudy(ntuple, maxEvents, opt.outFile)
        exit()

    tot_nevents = 0
    tot_genpart = 0
    tot_genjet = 0
    tot_electron = 0
    tot_gamma = 0
    tot_muon = 0
    tot_jetchs = 0
    tot_jetpuppi = 0
    tot_tau = 0
    tot_met = 0
    tot_genjetAK8 = 0
    tot_jetAK8 = 0

    ## Set plotting parameters according to physics object
    params = {}
    outputF = TFile(opt.outFile, "RECREATE")
    obj = opt.physobject
    if obj=="jet": 
        print "You entered jet as the particle type -- please specify jetchs or jetpuppi"
        exit()
    elif obj=="jetchs" or obj=="jetpuppi":
        params = {
            "dR": 0.2,
            "ptRatio": 2.0,
            "ptMin": 20,
            "etaSlices": [[0, 1.3], [1.3, 2.5], [2.5, 3], [3, 5], [5,1e5] ], ## use 1e5 as "Inf"
            "ptSlices": [[20, 50], [50, 100], [100, 200], [200, 400], [400, 1e5] ],
            "sliceSplit": 1, # for 2D map, make N divisions of each slice
            "plotPtRange": [0, 1500],
            "plotEtaRange": [-5, 5],
            "plotPhiRange": [-5, 5],
            "plotMassRange": [0, 500],
            "plotNObjRange_Delp": [0, 20],
            "plotNObjRange_Full": [0, 50],
            "plotResoRange": [0.8, 1.2],
            "ids": [
                ## ["nameforplot", numerator idpass threshold, numerator isopass threshold, denominator: 0(all)/1(reco matched)/2(reco+id), "efficiency title"]
                ## NOTE: only efficiency plots get anything with value [3] > 0
                ## Loose is bit 0, Medium is bit 1, Tight is bit 2, -1 is nothing                
                ["reco",-1,-1,0,"#varepsilon(reco)"],                         ## reco (eff, fakerate, response)
                ["looseID",0,-1,0,"#varepsilon(reco)*#varepsilon(looseID)"], ## reco*ID (ID for fakerate)  
                ["tightID",2,-1,0,"#varepsilon(reco)*#varepsilon(tightID)"],
                ["looseIDifReco",0,-1,1,"#varepsilon(looseID)"],
                ["tightIDifReco",2,-1,1,"#varepsilon(tightID)"],      ## IDs on reco-matched gen (eff only)
                ], 
            }
        if dumptcl: params["sliceSplit"] = 2
    elif obj == "photon": 
        params = {
            "dR": 0.1,
            "ptRatio": 100.0,
            "ptMin": 8,
            "etaSlices": [[0, 1.5], [1.5, 3], [3, 4], [4,1e5]],
            "ptSlices": [[10, 20], [20, 50], [50, 100], [100, 150], [150, 1e5]],
            "sliceSplit": 3,
            "plotPtRange": [0, 250],
            "plotEtaRange": [-4, 4],
            "plotPhiRange": [-4, 4],
            "plotMassRange": [-1, 1],
            "plotNObjRange_Delp": [0, 4],
            "plotNObjRange_Full": [0, 4],
            "plotResoRange": [0.8, 1.2],
            "ids": [  
                ## ["nameforplot", numerator idpass threshold, numerator isopass threshold, 
                ##  denominator: 0(all)/1(reco matched)/2(reco+id), "x-axis label"]
                ## NOTE: only efficiency plots get anything with value [3] > 0 
                ## Loose is bit 0, Medium is bit 1, Tight is bit 2, -1 is nothing
                ["reco",-1,-1,0,"#varepsilon(reco)"],                         ## reco (eff, fakerate, response)
                ["looseID",0,-1,0,"#varepsilon(reco)*#varepsilon(looseID)"], ## reco*ID (ID for fakerate)  
                ["mediumID",1,-1,0,"#varepsilon(reco)*#varepsilon(mediumID)"],
                ["tightID",2,-1,0,"#varepsilon(reco)*#varepsilon(tightID)"],
                ["looseISO",-1,0,0,"#varepsilon(reco)*#varepsilon(looseISO)"],   ## reco*ISO (ISO for fakerate) 
                ["mediumISO",-1,1,0,"#varepsilon(reco)*#varepsilon(mediumISO)"],
                ["tightISO",-1,2,0,"#varepsilon(reco)*#varepsilon(tightISO)"],
                ["looseIDISO",0,0,0,"#varepsilon(reco)*#varepsilon(looseID)*#varepsilon(looseISO)"], ## reco*ID*ISOs (ID+ISO for fakerate)
                ["mediumIDISO",1,1,0,"#varepsilon(reco)*#varepsilon(mediumID)*#varepsilon(mediumISO)"], 
                ["tightIDISO",2,2,0,"#varepsilon(reco)*#varepsilon(tightID)*#varepsilon(tightISO)"], 
                ["looseIDifReco",0,-1,1,"#varepsilon(looseID)"], 
                ["mediumIDifReco",1,-1,1,"#varepsilon(mediumID)"],      ## IDs on reco-matched gen (eff only)
                ["tightIDifReco",2,-1,1,"#varepsilon(tightID)"],      ## IDs on reco-matched gen (eff only)
                ["looseISOifReco",-1,0,1,"#varepsilon(looseISO)"], 
                ["mediumISOifReco",-1,1,1,"#varepsilon(mediumISO)"],   ## ISOs on reco-matched gen (eff only) 
                ["tightISOifReco",-1,2,1,"#varepsilon(tightISO)"],   ## ISOs on reco-matched gen (eff only) 
                ["looseIDISOifReco",0,0,1,"#varepsilon(looseID)*#varepsilon(looseISO)"], 
                ["mediumIDISOifReco",1,1,1,"#varepsilon(mediumID)*#varepsilon(mediumISO)"], ## ID+ISOs on reco-matched gen (eff only)
                ["tightIDISOifReco",2,2,1,"#varepsilon(tightID)*#varepsilon(tightISO)"], ## ID+ISOs on reco-matched gen (eff only)
                ],
            }
        if dumptcl: params["sliceSplit"] = 2
    elif obj == "electron" or obj == "muon":
        params = {
            "dR": 0.2,
            "ptRatio": 2.0,
            "ptMin": 10,
            "etaSlices": [[0, 1.5], [1.5, 2.8], [2.8, 1e5] ],
            "ptSlices": [[10, 20], [20, 50], [50, 100], [100, 150], [150, 1e5] ],
            "sliceSplit": 2,
            "plotPtRange": [0, 250],
            "plotEtaRange": [-5, 5],
            "plotPhiRange": [-5, 5],
            "plotMassRange": [-1, 1],
            "plotNObjRange_Delp": [0, 8],
            "plotNObjRange_Full": [0, 8],
            "plotResoRange": [0.9, 1.1],
            "ids": [  
                ## ["nameforplot", numerator idpass threshold, numerator isopass threshold, 
                ##  denominator: 0(all)/1(reco matched)/2(reco+id), "efficiency title"]
                ## NOTE: only efficiency plots get anything with value [3] > 0 
                ## Loose is bit 0, Medium is bit 1, Tight is bit 2, -1 is nothing
                ["reco",-1,-1,0,"#varepsilon(reco)"],                         ## reco (eff, fakerate, response)
                ["looseID",0,-1,0,"#varepsilon(reco)*#varepsilon(looseID)"], ## reco*ID (ID for fakerate)  
                ["mediumID",1,-1,0,"#varepsilon(reco)*#varepsilon(mediumID)"],
                ["tightID",2,-1,0,"#varepsilon(reco)*#varepsilon(tightID)"],
                ["looseISO",-1,0,0,"#varepsilon(reco)*#varepsilon(looseISO)"],   ## reco*ISO (ISO for fakerate) 
                ["mediumISO",-1,1,0,"#varepsilon(reco)*#varepsilon(mediumISO)"],
                ["tightISO",-1,2,0,"#varepsilon(reco)*#varepsilon(tightISO)"],
                ["looseIDISO",0,0,0,"#varepsilon(reco)*#varepsilon(looseID)*#varepsilon(looseISO)"], ## reco*ID*ISOs (ID+ISO for fakerate)
                ["mediumIDISO",1,1,0,"#varepsilon(reco)*#varepsilon(mediumID)*#varepsilon(mediumISO)"], 
                ["tightIDISO",2,2,0,"#varepsilon(reco)*#varepsilon(tightID)*#varepsilon(tightISO)"], 
                ["looseIDifReco",0,-1,1,"#varepsilon(looseID)"], 
                ["mediumIDifReco",1,-1,1,"#varepsilon(mediumID)"],      ## IDs on reco-matched gen (eff only)
                ["tightIDifReco",2,-1,1,"#varepsilon(tightID)"],      ## IDs on reco-matched gen (eff only)
                ["looseISOifReco",-1,0,1,"#varepsilon(looseISO)"], 
                ["mediumISOifReco",-1,1,1,"#varepsilon(mediumISO)"],   ## ISOs on reco-matched gen (eff only) 
                ["tightISOifReco",-1,2,1,"#varepsilon(tightISO)"],   ## ISOs on reco-matched gen (eff only) 
                ["looseIDISOifReco",0,0,1,"#varepsilon(looseID)*#varepsilon(looseISO)"], 
                ["mediumIDISOifReco",1,1,1,"#varepsilon(mediumID)*#varepsilon(mediumISO)"], ## ID+ISOs on reco-matched gen (eff only)
                ["tightIDISOifReco",2,2,1,"#varepsilon(tightID)*#varepsilon(tightISO)"], ## ID+ISOs on reco-matched gen (eff only)
                ], 
            }
        if obj == 'electron': 
            #params["ptSlices"] = [[10,20], [20, 50], [50, 100], [100, 200], [200, 300], [300, 400], [400, 1e5]]
            params["etaSlices"] = [[0, 1.5], [1.5, 3], [3, 4], [4, 1e5] ]
        if dumptcl: params["sliceSplit"] = 2                
    else: 
        print 'Physics object not recognized! Choose jetchs, jetpuppi, photon, electron, or muon.'            
        exit()

    ## BOOK HISTOGRAMS
    hists = {} 
    hnames = ["pt", "eta", "phi", "mass", "idpass", "isopass"]
    for hname in hnames:
        if hname == "idpass": continue
        hists["gen"+obj+"_"+hname] = createHist(opt, "gen"+obj+"_"+hname,params)
        hists["gen"+obj+"_matched_"+hname] = createHist(opt, "gen"+obj+"_matched_"+hname,params)
    ## add IDs for reco hists
    for hname in hnames:
        if len(params["ids"]) == 0:
            hists[obj+"_"+hname] = createHist(opt, obj+"_"+hname,params)
            hists[obj+"_matched_"+hname] = createHist(opt, obj+"_matched_"+hname,params)
        else:
            for quality in params["ids"]:
                if quality[3] > 0: continue
                newname = hname+"_"+quality[0]
                hists[obj+"_"+newname] = createHist(opt, obj+"_"+newname,params)
                hists[obj+"_matched_"+newname] = createHist(opt, obj+"_matched_"+newname,params)
            
    cutList = ["nocut"]+params["etaSlices"]+params["ptSlices"]

    for cut in cutList:
        hname = "multiplicity"
        if len(params["ids"]) == 0:
            hname += "_"+ str(cut[0]) + "to" + str(cut[1])
            hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
            hists[obj+"_"+hname] = createHist(opt, obj+"_"+hname,params)
        else:
            for quality in params["ids"]:
                if quality[3] > 0: continue
                newname = hname+"_"+quality[0]+"_"+ str(cut[0]) + "to" + str(cut[1])
                newname = ((newname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                hists[obj+"_"+newname] = createHist(opt, obj+"_"+newname,params)

    ### book resolution histograms here:
    for ptbin in params["ptSlices"]:
        for etabin in params["etaSlices"]:            
            if len(params["ids"]) == 0:
                hname = "resolution_pt_{}_{}_eta_{}_{}".format(ptbin[0],  ptbin[1], etabin[0], etabin[1])
                hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                hists[obj+"_"+hname] = createHist(opt, obj+"_"+hname,params)
                print obj+"_"+hname
            else:
                for quality in params["ids"]:
                    if quality[3] > 0: continue
                    hname = "{}_resolution_pt_{}_{}_eta_{}_{}".format(quality[0], ptbin[0],  ptbin[1], etabin[0], etabin[1])
                    hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                    hists[obj+"_"+hname] = createHist(opt, obj+"_"+hname,params)

    for cut in ["nocut"]+params["etaSlices"]:
        hnames = ["efficiency_to_pt", "ptresponse_to_pt", "fakerate_to_pt"]
        for hname in hnames:
            if len(params["ids"]) == 0:
                title = "#varepsilon(reco)"
                hname += "_"+ str(cut[0]) + "to" + str(cut[1])
                hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                hists[obj+"_"+hname] = create2dHist(obj+"_"+hname,params,title)
            else:
                for quality in params["ids"]:
                    if ('ptresponse' in hname or 'fakerate' in hname) and quality[3] > 0: continue
                    newname = hname+"_"+quality[0]+"_"+ str(cut[0]) + "to" + str(cut[1])
                    newname = ((newname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                    hists[obj+"_"+newname] = create2dHist(obj+"_"+newname,params,quality[4])

    for cut in ["nocut"]+params["ptSlices"]:
        hnames = ["efficiency_to_eta", "ptresponse_to_eta", "fakerate_to_eta"]
        for hname in hnames:
            if len(params["ids"]) == 0:
                title = "#varepsilon(reco)"
                hname += "_"+ str(cut[0]) + "to" + str(cut[1])
                hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                hists[obj+"_"+hname] = create2dHist(obj+"_"+hname,params,title)
            else:
                for quality in params["ids"]:
                    if ('ptresponse' in hname or 'fakerate' in hname) and quality[3] > 0: continue
                    newname = hname+"_"+quality[0]+"_"+ str(cut[0]) + "to" + str(cut[1])
                    newname = ((newname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                    hists[obj+"_"+newname] = create2dHist(obj+"_"+newname,params,quality[4])

    hnames = ["efficiency2D", "fakerate2D"]
    for hname in hnames:
        if len(params["ids"]) == 0:
            title = "#varepsilon(reco)"
            hists[obj+"_"+hname] = create2Dmap(obj+"_"+hname,params,title,dumptcl)
        else:
            for quality in params["ids"]:
                if 'fakerate' in hname and quality[3] > 0: continue
                newname = hname+"_"+quality[0]
                hists[obj+"_"+newname] = create2Dmap(obj+"_"+newname,params,quality[4],dumptcl)
   

    ## LOOP over events
    for event in ntuple:
        if maxEvents > 0 and event.entry() >= maxEvents:
            break
        if (tot_nevents %1000) == 0 :
            print '... processed {} events ...'.format(event.entry()+1)

        tot_nevents += 1
        tot_genpart += len(event.genparticles())
        tot_genjet += len(event.genjets())
        tot_electron += len(event.electrons())
        tot_gamma += len(event.gammas())
        tot_muon += len(event.muons())
        tot_jetchs += len(event.jetschs())
        tot_jetpuppi += len(event.jetspuppi())
        tot_tau += len(event.taus())
        tot_met += len(event.metspuppi())
        #tot_genjetAK8 += len(event.genjetsAK8())
        #tot_jetAK8 += len(event.jetsAK8())

        ## Set the reco and generated object collections
	if obj=="jetpuppi":
            recoobjs = event.jetspuppi()
            genobjs = event.genjets()
	    fakeobjs = event.jetspuppi()	
	elif obj=="jetchs":
            recoobjs = event.jetschs()
            genobjs = event.genjets()
	    fakeobjs = event.jetschs()
	elif obj == "photon": 
            recoobjs = event.gammas()
            genobjs = event.genparticles()
            fakeobjs = event.jetspuppi()
        elif obj == "electron":
            recoobjs = event.electrons()
            genobjs = event.genparticles()
            fakeobjs = event.jetspuppi()
        elif obj == "muon":
            recoobjs = event.muons()
            genobjs = event.genparticles()
            fakeobjs = event.jetspuppi()
        else: 
            print 'Physics object not recognized! Choose jet, photon, electron, or muon.'            

        ## Initialize multiplicity counters
        multiplicity = {}
        for cut in cutList:
            cutname = str(cut[0]) + "to" + str(cut[1])
            cutname = ((cutname.replace('.','p')).replace('100000p0','Inf')).replace('ntoo','nocut')
            if len(params["ids"]) > 0:
                for quality in params["ids"]:                    
                    if quality[3] == 0: multiplicity[cutname+"_"+quality[0]] = 0                    
            else: multiplicity[cutname] = 0

        p_tvectors = []
        p_idpass = []
        p_isopass = []

        #printgen = False

        ## Loop over reco objects
        for p in recoobjs:
            if abs(p.eta()) > 5 or p.pt() < params["ptMin"] : continue

            ## jets don't have the isopass method            
            ## Dummy value is 1111 = 8+4+2+1 = 15
            isopass = 15   
            try: isopass = p.isopass() 
            except: pass

            ## If this is fullsim, for electrons and photons we want isopass = 1111
            if (obj == 'photon' or obj == 'electron') and 'full' in opt.outFile: 
                isopass = 15

            ## Fill reco object hists
            if len(params["ids"]) > 0:
                for quality in params["ids"]:
                    if quality[3] > 0: continue
                    if p.idpass() > quality[1] and isopass > quality[2]:
                        hists[obj+"_pt_"+quality[0]].Fill(p.pt())
                        hists[obj+"_eta_"+quality[0]].Fill(p.eta())
                        hists[obj+"_phi_"+quality[0]].Fill(p.phi())
                        hists[obj+"_mass_"+quality[0]].Fill(p.mass())
                        hists[obj+"_idpass_"+quality[0]].Fill(p.idpass())
                        hists[obj+"_isopass_"+quality[0]].Fill(isopass)
            else:
                hists[obj+"_pt"].Fill(p.pt())
                hists[obj+"_eta"].Fill(p.eta())
                hists[obj+"_phi"].Fill(p.phi())
                hists[obj+"_mass"].Fill(p.mass())
                hists[obj+"_idpass"].Fill(p.idpass())
                hists[obj+"_isopass"].Fill(isopass)


            if obj == "jet" and p.pt() < 25 : continue  # for jets
            
            ## Increment multiplicity counters
            if len(params["ids"]) > 0:
                for quality in params["ids"]: 
                    if quality[3] >= 1: continue
                    if (quality[1] < 0 or bool(p.idpass() & (1<<quality[1]))) and (quality[2] < 0 or bool(isopass & (1<<quality[2]))): multiplicity["nocut_"+quality[0]] += 1
            else: multiplicity["nocut"] += 1
            for cut in params["etaSlices"]:
                cutname = str(cut[0]) + "to" + str(cut[1])
                cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                if cut[0] < abs(p.eta()) <= cut[1] : 
                    if len(params["ids"]) > 0:
                        for quality in params["ids"]:
                            if quality[3] >= 1: continue 
                            if (quality[1] < 0 or bool(p.idpass() & (1<<quality[1]))) and (quality[2] < 0 or bool(isopass & (1<<quality[2]))): multiplicity[cutname+"_"+quality[0]] += 1
                    else: multiplicity[cutname] += 1

            for cut in params["ptSlices"]:
                cutname = str(cut[0]) + "to" + str(cut[1])
                cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                if  cut[0] <= p.pt() < cut[1]: 
                    if len(params["ids"]) > 0:
                        for quality in params["ids"]: 
                            if quality[3] >= 1: continue
                            if (quality[1] < 0 or bool(p.idpass() & (1<<quality[1]))) and (quality[2] < 0 or bool(isopass & (1<<quality[2]))): multiplicity[cutname+"_"+quality[0]] += 1
                    else: multiplicity[cutname] += 1

            ## STORE all reco objects passing basic thresholds (25 hardcoded for jets)
            p_vec = TLorentzVector()
            p_vec.SetPtEtaPhiM(p.pt(), p.eta(), p.phi(), p.mass())
            p_tvectors.append(p_vec)
            p_idpass.append(p.idpass())
            p_isopass.append(isopass)


        ## For lepton/photon only calculate efficiency, response, resolution in signal file
        if (obj != 'photon' and obj != 'electron' and obj != 'muon') or 'QCD' not in inFile:

            ## LOOP over the GEN objects
            for g in genobjs:
        
                ## Cuts on the gen object
                if abs(g.eta()) > 5 or g.pt() < params["ptMin"] : continue
                if obj in pdgid:
                    if abs(g.pid()) != pdgid[obj]: continue  # check genparticle pid  
                    if obj != 'photon' and g.status() != 1: continue
                    if obj == 'photon' and genobjs[g.m1()].pid() != 25: continue # always 2 if status 1 not required!
        
                ## Fill gen object hists
                hists["gen"+obj+"_pt"].Fill(g.pt())
                hists["gen"+obj+"_eta"].Fill(g.eta())
                hists["gen"+obj+"_phi"].Fill(g.phi())
                hists["gen"+obj+"_mass"].Fill(g.mass())
        
                g_vec = TLorentzVector()
                g_vec.SetPtEtaPhiM(g.pt(), g.eta(), g.phi(), g.mass())
                match = 0
                matchindex = -1
                minDR = 999
                minDRindex = -1
        
                ## Find matched reco object with minimum DR
                for ivec in range(0, len(p_tvectors)):
                    deltaR = g_vec.DeltaR(p_tvectors[ivec])
                    if deltaR < minDR:
                        minDR = deltaR
                        minDRindex = ivec
        
                if minDR < params["dR"] and ( 1./params["ptRatio"] < p_tvectors[minDRindex].Pt()/g.pt() < params["ptRatio"]) : # matched
                    match = 1
                    matchindex = minDRindex
                
                ## Work with only matched pairs first:
                if match == 1:
                    
                    ## Fill matched reco and gen hists
                    if len(params["ids"]) > 0:
                        for quality in params["ids"]:
                            if quality[3] >= 1: continue
                            if p_idpass[matchindex] > quality[1] and p_isopass[matchindex] > quality[2]:
                                hists[obj+"_matched_pt_"+quality[0]].Fill(p_tvectors[matchindex].Pt())
                                hists[obj+"_matched_eta_"+quality[0]].Fill(p_tvectors[matchindex].Eta())
                                hists[obj+"_matched_phi_"+quality[0]].Fill(p_tvectors[matchindex].Phi())
                                hists[obj+"_matched_mass_"+quality[0]].Fill(p_tvectors[matchindex].M())
                                hists[obj+"_matched_idpass_"+quality[0]].Fill(p_idpass[matchindex])
        
                    else:
                        hists[obj+"_matched_pt"].Fill(p_tvectors[matchindex].Pt())
                        hists[obj+"_matched_eta"].Fill(p_tvectors[matchindex].Eta())
                        hists[obj+"_matched_phi"].Fill(p_tvectors[matchindex].Phi())
                        hists[obj+"_matched_mass"].Fill(p_tvectors[matchindex].M())
                        hists[obj+"_matched_idpass"].Fill(p_idpass[matchindex]) 
                    hists["gen"+obj+"_matched_pt"].Fill(g.pt())
                    hists["gen"+obj+"_matched_eta"].Fill(g.eta())
                    hists["gen"+obj+"_matched_phi"].Fill(g.phi())
                    hists["gen"+obj+"_matched_mass"].Fill(g.mass())
            
                    ## Fill ptresponse hists and resolution plots              
                    if len(params["ids"]) > 0:
                        for quality in params["ids"]:
                            if quality[3] >= 1: continue
                            if (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1]))) and (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2]))):
                                hists[obj+"_ptresponse_to_eta_"+quality[0]].Fill(g.eta(), p_tvectors[matchindex].Pt()/g.pt())
                                hists[obj+"_ptresponse_to_pt_"+quality[0]].Fill(g.pt(), p_tvectors[matchindex].Pt()/g.pt())
        
                                ## here fill resolution 
                                for ptbin in params["ptSlices"]:
                                    for etabin in params["etaSlices"]:
                                        if g.pt() > ptbin[0] and g.pt() < ptbin[1] and abs(g.eta()) > etabin[0] and abs(g.eta()) < etabin[1] :
                                            hname = "{}_resolution_pt_{}_{}_eta_{}_{}".format(quality[0], ptbin[0],  ptbin[1], etabin[0], etabin[1])
                                            hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                                            hists[obj+"_"+hname].Fill(p_tvectors[matchindex].Pt()/g.pt())
        
                    else:
                        hists[obj+"_ptresponse_to_eta"].Fill(g.eta(), p_tvectors[matchindex].Pt()/g.pt())
                        hists[obj+"_ptresponse_to_pt"].Fill(g.pt(), p_tvectors[matchindex].Pt()/g.pt())
        
                        for ptbin in params["ptSlices"]:
                            for etabin in params["etaSlices"]:
                                if g.pt() > ptbin[0] and g.pt() < ptbin[1] and abs(g.eta()) > etabin[0] and abs(g.eta()) < etabin[1] :
        
                                    hname = "resolution_pt_{}_{}_eta_{}_{}".format(ptbin[0],  ptbin[1], etabin[0], etabin[1])
                                    hname = ((hname.replace('.', 'p')).replace('100000p0','Inf')).replace('_ntoo','')
                                    hists[obj+"_"+hname].Fill(g.pt(), p_tvectors[matchindex].Pt()/g.pt())
        
                    for cut in params["ptSlices"]:
                        cutname = str(cut[0]) + "to" + str(cut[1])
                        cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                        if cut[0] <= g.pt() < cut[1]: 
                            if len(params["ids"]) > 0:
                                for quality in params["ids"]:
                                    if quality[3] >= 1: continue
                                    if (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1]))) and (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2]))): 
                                        hists[obj+"_ptresponse_to_eta_"+quality[0]+"_"+cutname].Fill(g.eta(), p_tvectors[matchindex].Pt()/g.pt())
                            else: hists[obj+"_ptresponse_to_eta_"+cutname].Fill(g.eta(), p_tvectors[matchindex].Pt()/g.pt())
                    
                    for cut in params["etaSlices"]:
                            cutname = str(cut[0]) + "to" + str(cut[1])
                            cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                            if cut[0] < abs(g.eta()) <= cut[1]: 
                                if len(params["ids"]) > 0:
                                    for quality in params["ids"]:
                                        if quality[3] >= 1: continue
                                        if (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1]))) and (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2]))):
                                            hists[obj+"_ptresponse_to_pt_"+quality[0]+"_"+cutname].Fill(g.pt(), p_tvectors[matchindex].Pt()/g.pt())
                                else: hists[obj+"_ptresponse_to_pt_"+cutname].Fill(g.pt(), p_tvectors[matchindex].Pt()/g.pt())
        
        
                    ## end of matched object stuff
        
                ## working with matched AND unmatched: fill match status into efficiency TProfiles
                ## efficiency when quality[3] == 0:
                ##             denominator = all gen objects: fill 0's for unmatched, 0's for matched and reco obj fails quality, match*idpass*isopass = 0
                ##             numerator = all reco-matched gen objects with given reco quality: fill 1's for matched and reco obj passes quality, match*idpass*isopass = 1
                ## efficiency when quality[3] == 1: 
                ##             denominator = all reco-matched gen objects: if match, fill 0 if matched&!quality, idpass*isopass = 0
                ##             numerator = all reco-matched gen objects with given reco quality: fill 1 if matched&quality, idpass*isopass = 1
                #print '*************************************'
                if len(params["ids"]) > 0:
                    for quality in params["ids"]:

                        try: idpass = (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1])))
                        except IndexError: idpass = False
                        try: isopass = (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2])))
                        except: isopass = False
                        
                        if quality[3] >= 1:
                            if match == 1:
                                if quality[3] == 2:
                                    if idpass:
                                        hists[obj+"_efficiency_to_eta_"+quality[0]].Fill(g.eta(), isopass) #0 if iso fails, 1 if passes
                                        hists[obj+"_efficiency_to_pt_"+quality[0]].Fill(g.pt(), isopass)
                                        hists[obj+"_efficiency2D_"+quality[0]].Fill(g.pt(),g.eta(), isopass)
                                else:
                                    hists[obj+"_efficiency_to_eta_"+quality[0]].Fill(g.eta(), idpass*isopass) #0 if either fails, 1 if both
                                    hists[obj+"_efficiency_to_pt_"+quality[0]].Fill(g.pt(), idpass*isopass)
                                    hists[obj+"_efficiency2D_"+quality[0]].Fill(g.pt(),g.eta(), idpass*isopass)
                        else:
                            hists[obj+"_efficiency_to_eta_"+quality[0]].Fill(g.eta(), match*idpass*isopass) #0 if any fail, 1 if all
                            hists[obj+"_efficiency_to_pt_"+quality[0]].Fill(g.pt(), match*idpass*isopass)
                            hists[obj+"_efficiency2D_"+quality[0]].Fill(g.pt(),g.eta(), match*idpass*isopass)
                else:
                    hists[obj+"_efficiency_to_eta"].Fill(g.eta(), match)
                    hists[obj+"_efficiency_to_pt"].Fill(g.pt(), match)
                    hists[obj+"_efficiency2D"].Fill(g.pt(),g.eta(), match)
                for cut in params["ptSlices"]:
                    cutname = str(cut[0]) + "to" + str(cut[1])
                    cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                    if cut[0] <= g.pt() < cut[1]: 
                        if len(params["ids"]) > 0:
                            for quality in params["ids"]:
                                try: idpass = (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1])))
                                except IndexError: idpass = False
                                try: isopass = (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2])))
                                except: isopass = False
                                if quality[3] >= 1:
                                    if match == 1: 
                                        if quality[3] == 2:
                                            if idpass: hists[obj+"_efficiency_to_eta_"+quality[0]+"_" + cutname].Fill(g.eta(), isopass)
                                        else: hists[obj+"_efficiency_to_eta_"+quality[0]+"_" + cutname].Fill(g.eta(), idpass*isopass)
                                else: hists[obj+"_efficiency_to_eta_"+quality[0]+"_" + cutname].Fill(g.eta(), match*idpass*isopass)
                        else: hists[obj+"_efficiency_to_eta_" + cutname].Fill(g.eta(), match)
        
                for cut in params["etaSlices"]:
                    cutname = str(cut[0]) + "to" + str(cut[1])
                    cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                    if cut[0] < abs(g.eta()) <= cut[1]: 
                        if len(params["ids"]) > 0:
                            for quality in params["ids"]:
                                try: idpass = (quality[1] < 0 or bool(p_idpass[matchindex] & (1<<quality[1])))
                                except IndexError: idpass = False
                                try: isopass = (quality[2] < 0 or bool(p_isopass[matchindex] & (1<<quality[2])))
                                except: isopass = False
                                if quality[3] >= 1:
                                    if match == 1: 
                                        if quality[3] == 2:
                                            if idpass: hists[obj+"_efficiency_to_pt_"+quality[0]+"_"+cutname].Fill(g.pt(), isopass)
                                        else: hists[obj+"_efficiency_to_pt_"+quality[0]+"_"+cutname].Fill(g.pt(), idpass*isopass)
                                else: hists[obj+"_efficiency_to_pt_"+quality[0]+"_"+cutname].Fill(g.pt(), match*idpass*isopass)
                        else: hists[obj+"_efficiency_to_pt_"+cutname].Fill(g.pt(), match)
        
                ## remove this matched reco object so later gen objects can't be matched to it
                if matchindex > -1:
                    p_tvectors.pop(matchindex)
                    p_idpass.pop(matchindex)
                    p_isopass.pop(matchindex)
        
                ## end of gen object loop
            ## end of check that this is a signal file for lepton/photon

        ## For lepton/photon, only calculate fake rates in QCD
        if (obj != 'photon' and obj != 'electron' and obj != 'muon') or 'QCD' in inFile:

            ## LOOP over the JETS
            for g in fakeobjs:
        
                ## Cuts on the gen fake object
                if abs(g.eta()) > 5 or g.pt() < 15 : continue
        
                g_vec = TLorentzVector()
                g_vec.SetPtEtaPhiM(g.pt(), g.eta(), g.phi(), g.mass())
                matchF = 0
                matchindexF = -1
                minDRF = 999
                minDRindexF = -1
                
                ## Find matched fake reco object with minimum DR -- this list has all gen matches removed
                ## If photon/elec/muon, there were no gen matches to remove because this is QCD!
                for ivec in range(0, len(p_tvectors)):
                    deltaR = g_vec.DeltaR(p_tvectors[ivec])
                    if deltaR < minDRF:
                        minDRF = deltaR
                        minDRindexF = ivec
        
                if minDRF < 0.4: # matched within radius of jet
                    matchF = 1
                    matchindexF = minDRindexF
        
                if len(params["ids"]) > 0:
                    for quality in params["ids"]:
                        if quality[3] > 0: continue
                        try: idpass = (quality[1] < 0 or bool(p_idpass[matchindexF] & (1<<quality[1])))
                        except IndexError: idpass = False
                        try: isopass = (quality[2] < 0 or bool(p_isopass[matchindexF] & (1<<quality[2])))
                        except: isopass = False
                        
                        hists[obj+"_fakerate_to_eta_"+quality[0]].Fill(g.eta(), matchF*idpass*isopass) #0 if any fail, 1 if all
                        hists[obj+"_fakerate_to_pt_"+quality[0]].Fill(g.pt(), matchF*idpass*isopass)
                        hists[obj+"_fakerate2D_"+quality[0]].Fill(g.pt(),g.eta(), matchF*idpass*isopass)
                else:
                    hists[obj+"_fakerate_to_eta"].Fill(g.eta(), matchF)
                    hists[obj+"_fakerate_to_pt"].Fill(g.pt(), matchF)
                    hists[obj+"_fakerate2D"].Fill(g.pt(),g.eta(), matchF)
                for cut in params["ptSlices"]:
                    cutname = str(cut[0]) + "to" + str(cut[1])
                    cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                    if cut[0] <= g.pt() < cut[1]: 
                        if len(params["ids"]) > 0:
                            for quality in params["ids"]:
                                if quality[3] > 0: continue
                                try: idpass = (quality[1] < 0 or bool(p_idpass[matchindexF] & (1<<quality[1])))
                                except IndexError: idpass = False
                                try: isopass = (quality[2] < 0 or bool(p_isopass[matchindexF] & (1<<quality[2])))
                                except: isopass = False
                                hists[obj+"_fakerate_to_eta_"+quality[0]+"_" + cutname].Fill(g.eta(), matchF*idpass*isopass)
                        else: hists[obj+"_fakerate_to_eta_" + cutname].Fill(g.eta(), matchF)
        
                for cut in params["etaSlices"]:
                        cutname = str(cut[0]) + "to" + str(cut[1])
                        cutname = (cutname.replace('.','p')).replace('100000p0','Inf')
                        if cut[0] < abs(g.eta()) <= cut[1]: 
                            if len(params["ids"]) > 0:
                                for quality in params["ids"]:
                                    if quality[3] > 0: continue
                                    try: idpass = (quality[1] < 0 or bool(p_idpass[matchindexF] & (1<<quality[1])))
                                    except IndexError: idpass = False
                                    try: isopass = (quality[2] < 0 or bool(p_isopass[matchindexF] & (1<<quality[2])))
                                    except: isopass = False
                                    hists[obj+"_fakerate_to_pt_"+quality[0]+"_"+cutname].Fill(g.pt(), matchF*idpass*isopass)
                            else: hists[obj+"_fakerate_to_pt_"+cutname].Fill(g.pt(), matchF)
        
                ## remove this matched reco object so later gen objects can't be matched to it
                if matchindexF > -1:
                    p_tvectors.pop(matchindexF)
                    p_idpass.pop(matchindexF)
                    p_isopass.pop(matchindexF)
                

        ## for each evt
        for cut in cutList:
            hname = "multiplicity"
            cutname = str(cut[0]) + "to" + str(cut[1])
            cutname = ((cutname.replace('.','p')).replace('100000p0','Inf')).replace('ntoo','nocut')
            if len(params["ids"]) > 0: 
                for quality in params["ids"]:
                    if quality[3] > 0: continue
                    hname = "multiplicity_"+quality[0]
                    if cutname != "nocut": hname += "_"+cutname                  
                    hists[obj+"_" + hname].Fill(multiplicity[cutname+"_"+quality[0]])
            else: 
                if cutname != "nocut": hname += "_"+ cutname
                hists[obj+"_" + hname].Fill(multiplicity[cutname])
            

    ## Write all histograms
    outputF.cd()
    for h in hists.keys():
        hists[h].Write()


    print("Processed %d events" % tot_nevents)
    print("On average %f generator particles" % (float(tot_genpart) / tot_nevents))
    print("On average %f generated jets" % (float(tot_genjet) / tot_nevents))
    print("On average %f electrons" % (float(tot_electron) / tot_nevents))
    print("On average %f photons" % (float(tot_gamma) / tot_nevents))
    print("On average %f muons" % (float(tot_muon) / tot_nevents))
    print("On average %f chs jets" % (float(tot_jetchs) / tot_nevents))
    print("On average %f puppi jets" % (float(tot_jetpuppi) / tot_nevents))
    print("On average %f taus" % (float(tot_tau) / tot_nevents))
    print("On average %f met" % (float(tot_met) / tot_nevents))
    #print("On average %f generated AK8 jets" % (float(tot_genjetAK8) / tot_nevents))
    #print("On average %f jetsAK8" % (float(tot_jetAK8) / tot_nevents))

if __name__ == "__main__":
    main()

