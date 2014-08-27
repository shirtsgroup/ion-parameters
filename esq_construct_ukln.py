from basisanalyze import *
import numpy
from numpy import ma
from scipy.integrate import simps
from scipy import linspace
from scipy import logspace
import scipy.optimize
import matplotlib.pyplot as plt
import os.path
import pdb
import simtk.unit as units
from pymbar import MBAR
from numpy import linalg
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable as mal
import time
import datetime
import sys
from mpl_toolkits.mplot3d import axes3d
import timeseries

kB = units.BOLTZMANN_CONSTANT_kB * units.AVOGADRO_CONSTANT_NA
T = 298 * units.kelvin
kT = kB*T
kjpermolTokT = units.kilojoules_per_mole / kT
kjpermolTokcal = 1/4.184
graphsfromfile=True #Generate graphs from the .npz arrays
savedata = False #Save dhdl data
masked=False
load_ukln = True
timekln = False #Timing information
subsample_method = 'per-state'

#logspace or linspace
narg = len(sys.argv)
if narg > 1:
    if sys.argv[1] == 'log':
        spacing=logspace
    elif sys.argv[1] == 'lin':
        spacing=linspace
    else:
        spacing=linspace
else:
    spacing=linspace

#Main output controling vars:
#nstate options: 24, 32, 40, 49
nstates = 26
Nparm = 51 #51, 101, or 151
plotReal = False
sig_factor=1
annotatefig = False
savefigs = False
if Nparm == 151 or True:
    alle = True
else:
   alle = False

sig_min = 0.1 #nm
sig_max = 1.2
sig3_samp_space = linspace(sig_min**3, sig_max**3, nstates)
sig_samp_space = sig3_samp_space**(1.0/3)
sig_min = 0.25 #updated for 
sig_samp_space[0] = sig_min
sig3_samp_space[0] = sig_samp_space[0]**3
epsi_min = 0.1 #kJ/mol
epsi_max = 1.2
q_min = -3.0
q_max = +3.0
epsi_samp_space = linspace(epsi_min, epsi_max, 11)
lamto_epsi = lambda lam: (epsi_max - epsi_min)*lam + epsi_min
lamto_sig3 = lambda lam: (sig_max**3 - sig_min**3)*lam + sig
lamto_sig = lambda lam: lamto_sig3(lam)**(1.0/3)


#epsi_samp_space = numpy.array([0.100, 6.960, 2.667, 1.596, 1.128, 0.870, 0.706, 0.594, 0.513, 0.451, 0.40188])
#sig_samp_space = numpy.array([0.25000, 0.41677, 0.58856, 0.72049, 0.83175, 0.92978, 1.01843, 1.09995, 1.17584, 1.24712, 1.31453])
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#This is the true sigma sampling space because I made a small math error when initially spacing 
#                                0           1            2            3            4            5            6            7            8            9   10   11
sig_samp_space = numpy.array([0.25, 0.57319535, 0.712053172, 0.811158734, 0.890612296, 0.957966253, 1.016984881, 1.069849165, 1.117949319, 1.162232374, 1.2, 0.3])
epsi_samp_space = numpy.append(epsi_samp_space, 0.8)
#more                                                    12           13           14           15           16           17           18           19           20           21           22           23
sig_samp_space  = numpy.append(sig_samp_space, [1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881, 1.016984881])
epsi_samp_space = numpy.append(epsi_samp_space,[       0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76,        0.76])
#Even more                                              24          25          26          27          28          29          30          31
sig_samp_space  = numpy.append(sig_samp_space, [0.73518161, 0.64603911, 0.63626708, 1.13315949, 0.65545451, 0.77026625, 0.66490831, 0.87519838])
epsi_samp_space = numpy.append(epsi_samp_space,[0.56087413, 1.70893940, 2.94070444, 2.28313607, 2.90508252, 0.52984658, 1.64047376,        0.1])
#MOAR!!!                                                32          33          34          35          36          37          38          39
sig_samp_space  = numpy.append(sig_samp_space, [0.63122622, 0.69343482, 0.64792833, 1.13099574, 0.84507822, 0.56842670, 0.66070435, 1.14216356])
epsi_samp_space = numpy.append(epsi_samp_space,[2.90747632, 0.36510159, 1.60992045, 2.27698065, 0.54290845, 0.61327658, 2.54037597, 2.34264248])
#Ions 40-48                                             40          41          42          43          44          45          46          47          48
sig_samp_space  = numpy.append(sig_samp_space, [0.64665028, 0.73480072, 0.63877148, 1.13300771, 0.80047188, 0.70852054, 0.69411112, 1.16566948, 1.13144229])
epsi_samp_space = numpy.append(epsi_samp_space,[1.70926312, 0.55844222, 2.94301283, 2.32384021, 0.54958776, 1.69642936, 2.93903566, 2.58729246, 2.26568506])
sig3_samp_space = sig_samp_space**3
#                                0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,   12,   13,   14,   15,   16,   17,   18,   19,   20,   21,   22,   23 
q_samp_space    = numpy.array([  0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  0,  0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, +0.5, +1.0, +1.5, +2.0, +2.5, +3.0])
#                                                  24,      25,      26,      27,      28,      29,      30,      31
q_samp_space    = numpy.append(q_samp_space, [-2.0378, -1.9570, -1.9815, -2.2338, +1.7152, +1.7631, +1.7121, -0.5294])
#                                                  32       33       34       35       36       37       38       39
q_samp_space    = numpy.append(q_samp_space, [-1.9345, -1.9824, -1.9437, -2.1985,  2.2127,  2.0717,  1.6390,  1.9957])
#                                                  40       41       42       43      44      45      46      47      48
q_samp_space    = numpy.append(q_samp_space, [-1.9349, -2.0152, -1.9457, -2.2014, 1.7741, 1.7121, 1.4084, 1.1643, 2.5955])
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#Real molecule sampling
realname = ['UAm', 'NOP', 'C60', 'LJ6', 'null', 'LJ11']
nreal = len(realname)
realepsi = numpy.array([1.2301, 3.4941, 1.0372, 0.7600, 0, 0.8])
realsig  = numpy.array([0.3730, 0.6150, 0.9452, 1.0170, 0, 0.3])
realq    = numpy.array([     0,      0,      0,      0, 0,   0])

#epsi_max = 0.40188
#sig_max = 1.31453

if spacing is logspace:
    StartSpace = -5
    EndSpace   = 0
    spacename='log'
    PlotStart = 10**StartSpace
    PlotEnd   = 10**EndSpace
elif spacing is linspace:
    sigStartSpace = sig_min
    sigEndSpace   = sig_max
    epsiStartSpace = epsi_min
    qStartSpace = q_min
    qEndSpace = q_max
    if alle:
        epsiEndSpace   = 3.6 #!!! Manual set
    else:
        epsiEndSpace   = epsi_max
    spacename='linear'
    sigPlotStart = sigStartSpace**sig_factor
    sigPlotEnd   = sigEndSpace**sig_factor
    epsiPlotStart = epsiStartSpace
    epsiPlotEnd   = epsiEndSpace
    qPlotStart = qStartSpace
    qPlotEnd = qEndSpace


################ SUBROUTINES ##################
def my_annotate(ax, s, xy_arr=[], *args, **kwargs):
  ans = []
  an = ax.annotate(s, xy_arr[0], *args, **kwargs)
  ans.append(an)
  d = {}
  try:
    d['xycoords'] = kwargs['xycoords']
  except KeyError:
    pass
  try:
    d['arrowprops'] = kwargs['arrowprops']
  except KeyError:
    pass
  for xy in xy_arr[1:]:
    an = ax.annotate(s, xy, alpha=0.0, xytext=(0,0), textcoords=an, **d)
    ans.append(an)
  return ans

############### Lloyd's Algorithm for voronoi tesalation ############
'''
This block is designed to help me id where the center of a volume of a given feature is
Based on datasicnelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python
'''
import random
def cluster_points(X,mu):
    clusters={}
    for x in X:
        bestmukey = min([(i[0], numpy.linalg.norm(x-mu[i[0]])) for i in enumerate(mu)], key=lambda t:t[1])[0]
        try:
            clusters[bestmukey].append(x)
        except KeyError:
            clusters[bestmukey]=[x]
    for key in clusters.keys(): #Convert to single array, not a set of arrays
        clusters[key] = numpy.array(clusters[key])
    return clusters
def reevaluate_centers(clusters, weights):
    newmu=[]
    keys= sorted(clusters.keys())
    for k in keys:
        #Convert a set of clusters to their tuple form to feed into the weights
        weight_map = tuple(clusters[k][:,i] for i in range(clusters[k].shape[1])) #shape[1] is the N dim
        #Identify where this cluster is
        tempfeatures = numpy.zeros(weights.shape)
        tempfeatures[weight_map] = 1
        #Find the center of mass based on the weights
        com = numpy.array(ndimage.measurements.center_of_mass(weights, labels=tempfeatures, index=1))
        #Attach these weights to the new mu
        newmu.append(com)
        #newmu.append(numpy.mean(clusters[k],axis=0))
    return newmu
def has_converged(mu,oldmu):
    try:
        converged = (set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu]))
    except:
        converged = (set([a for a in mu]) == set([a for a in oldmu]))
    return converged
def find_centers(X, K, weights, verbose=False):
    #Initilize to K random centers
    oldmu =  random.sample(X,K)
    mu = random.sample(X,K)
    #oldmu = [weights[tuple(j for j in i)] for i in oldcord] #Create the list of weights by pulling each "center" and then making the tuple index of the single entry before passing it to weights
    #mu = [weights[tuple(j for j in i)] for i in mucord]
    iteration = 1
    while not has_converged(mu,oldmu):
        if verbose: print "Iteration: %i" % iteration
        oldmu=mu
        #assign all points in X to clusters
        clusters = cluster_points(X,mu)
        #Re-evaluate centers
        mu = reevaluate_centers(clusters, weights)
        iteration += 1
    return mu, clusters
def closest_index(point, features, index):
    #Find the closest point in features at index that is near point.
    #Point should have dimensions to describe a point in features
    #Create array of feature indices
    feature_loc = numpy.where(features == index)
    NFPoints = len(feature_loc[0])
    Ndim = point.shape[0]
    indices = numpy.zeros([Ndim, NFPoints])
    delta = numpy.zeros(indices.shape)
    for dim in range(Ndim):
        indices[dim,:] = feature_loc[dim] #Should grab the array
        delta[dim,:] = feature_loc[dim] - point[dim] #Assign the delta operator
    distance = numpy.sqrt(numpy.sum(delta**2,axis = 0))
    minloc = numpy.where(distance == distance.min())
    return indices[:,minloc]

def printFreeEnergy(DeltaF_ij, dDeltaF_ij):
    nstates = DeltaF_ij.shape[0]
    print "%s DeltaF_ij:" % "complex"
    for i in range(nstates):
        for j in range(nstates):
            print "%8.3f" % DeltaF_ij[i,j],
        print ""
    print "%s dDeltaF_ij:" % "complex"
    for i in range(nstates):
        for j in range(nstates):
            print "%8.3f" % dDeltaF_ij[i,j],
        print ""
def normalizeData(data):
    data = data.astype(numpy.float)
    min = numpy.min(data)
    max = numpy.max(data)
    return (data - min)/ (max-min)

if __name__=="__main__":
    #generate sample length
    #dhdlstart = 34 #Row where data starts
    #dhdlenergy = 1 #column where energy is
    #dhdlstates = 4 #Column where dhdl to other states starts, also coulmn for U0
    g_en_start = 19 #Row where data starts in g_energy output
    g_en_energy = 1 #Column where the energy is located
    niterations = len(open('lj10/prod/energy10_10.xvg','r').readlines()[g_en_start:])
    #Min and max sigmas:
    fC12 = lambda epsi,sig: 4*epsi*sig**12
    fC6 = lambda epsi,sig: 4*epsi*sig**6
    fsig = lambda C12, C6: (C12/C6)**(1.0/6)
    fepsi = lambda C12, C6: C6**2/(4*C12)
    C12_delta = fC12(epsi_max, sig_max) - fC12(epsi_min, sig_min)
    C6_delta = fC6(epsi_max, sig_max) - fC6(epsi_min, sig_min)
    C12_delta_sqrt = fC12(epsi_max, sig_max)**.5 - fC12(epsi_min, sig_min)**.5
    C6_delta_sqrt = fC6(epsi_max, sig_max)**.5 - fC6(epsi_min, sig_min)**.5
    #Set up lambda calculation equations
    flamC6 = lambda epsi, sig: (fC6(epsi, sig) - fC6(epsi_min, sig_min))/C6_delta
    flamC12 = lambda epsi, sig: (fC12(epsi, sig) - fC12(epsi_min, sig_min))/C12_delta
    flamC6sqrt = lambda epsi, sig: (fC6(epsi, sig)**.5 - fC6(epsi_min, sig_min)**.5)/C6_delta_sqrt
    flamC12sqrt = lambda epsi, sig: (fC12(epsi, sig)**.5 - fC12(epsi_min, sig_min)**.5)/C12_delta_sqrt
    flamC1 = lambda q: q
    lamC12 = flamC12sqrt(epsi_samp_space, sig_samp_space)
    lamC6 = flamC6sqrt(epsi_samp_space, sig_samp_space)
    lamC1 = flamC1(q_samp_space)
    #Try to load u_kln
    sanity_kln = numpy.zeros([nstates,nstates,niterations])
    lam_range = linspace(0,1,nstates)
    if load_ukln and os.path.isfile('esq_ukln_consts_n%i.npz'%nstates):
        ukln_consts = numpy.load('esq_ukln_consts_n%i.npz'%nstates)
        u_kln = ukln_consts['u_kln']
        const_R_matrix = ukln_consts['const_R_matrix'] 
        const_A_matrix = ukln_consts['const_A_matrix'] 
        const_unaffected_matrix = ukln_consts['const_unaffected_matrix']
        const_q_matrix = ukln_consts['const_q_matrix']
        const_q2_matrix = ukln_consts['const_q2_matrix']
    else:
        #Initial u_kln
        u_kln = numpy.zeros([nstates,nstates,niterations])
        
        const_unaffected_matrix = numpy.zeros([nstates,niterations])
        const_Un_matrix = numpy.zeros([nstates,niterations])
        const_R0_matrix = numpy.zeros([nstates,niterations])
        const_R1_matrix = numpy.zeros([nstates,niterations])
        const_R_matrix = numpy.zeros([nstates,niterations])
        const_A0_matrix = numpy.zeros([nstates,niterations])
        const_A1_matrix = numpy.zeros([nstates,niterations])
        const_A_matrix = numpy.zeros([nstates,niterations])
        const_q_matrix = numpy.zeros([nstates,niterations])
        const_q2_matrix = numpy.zeros([nstates,niterations])
        #Read in the data for the unaffected state
        for k in xrange(nstates):
            print "Importing LJ = %02i" % k
            energy_dic = {'full':{}, 'rep':{}}
            energy_dic['null'] = open('lj%s/prod/energy%s_null.xvg' %(k,k),'r').readlines()[g_en_start:] #Read in the null energies (unaffected) of the K states
            for l in xrange(nstates):
                energy_dic['full']['%s'%l] = open('lj%s/prod/energy%s_%s.xvg' %(k,k,l),'r').readlines()[g_en_start:] #Read in the full energies for each state at KxL
                if l == 10 or l == 0:
                    energy_dic['rep']['%s'%l] = open('lj%s/prod/energy%s_%s_rep.xvg' %(k,k,l),'r').readlines()[g_en_start:] #Read in the repulsive energies at 0, nstates-1, and K
            energy_dic['q']  =  open('lj%s/prod/energy%s_q.xvg' %(k,k),'r').readlines()[g_en_start:] #Read in the charge potential energy
            energy_dic['q2']  =  open('lj%s/prod/energy%s_q2.xvg' %(k,k),'r').readlines()[g_en_start:] #Read in the charge potential energy
            #Fill in matricies
            for n in xrange(niterations):
                #Unaffected state
                const_Un_matrix[k,n] = float(energy_dic['null'][n].split()[g_en_energy])
                #Charge only state
                VI = float(energy_dic['q'][n].split()[g_en_energy]) - const_Un_matrix[k,n]
                VII = float(energy_dic['q2'][n].split()[g_en_energy]) - const_Un_matrix[k,n]
                q1 = 1
                q2 = 0.5
                QB = (q1**2*VII - q2**2*VI)/(q1**2*q2 - q2**2*q1)
                QA = (VI - q1*QB)/q1**2
                const_q_matrix[k,n] = QB
                const_q2_matrix[k,n] = QA
                #const_q_matrix[k,n] = float(energy_dic['q'][n].split()[g_en_energy]) - const_Un_matrix[k,n]
                #Isolate the data
                for l in xrange(nstates):
                    u_kln[k,l,n] = float(energy_dic['full']['%s'%l][n].split()[g_en_energy]) #extract the kln energy, get the line, split the line, get the energy, convert to float, store
                #Repulsive terms: 
                #R0 = U_rep[k,k,n] + dhdl[k,0,n] - Un[k,n]
                const_R0_matrix[k,n] = float(energy_dic['rep']['%s'%(0)][n].split()[g_en_energy]) - const_Un_matrix[k,n]
                #R1 = U_rep[k,k,n] + dhdl[k,-1,n] - Un[k,n]
                const_R1_matrix[k,n] = float(energy_dic['rep']['%s'%(10)][n].split()[g_en_energy]) - const_Un_matrix[k,n]
                const_R_matrix[k,n] = const_R1_matrix[k,n] - const_R0_matrix[k,n]
                #Finish the total unaffected term
                #Total unaffected = const_Un + U0 = const_Un + (U_full[k,0,n] - const_Un) = U_full[k,0,n]
                const_unaffected_matrix[k,n] = u_kln[k,0,n]
                #Fill in the q matrix
                
                #Attractive term
                #u_A = U_full[k,n] - constR[k,n] - const_unaffected[k,n]
                const_A0_matrix[k,n] = u_kln[k,0,n] - const_R0_matrix[k,n] - const_Un_matrix[k,n]
                const_A1_matrix[k,n] = u_kln[k,10,n] - const_R1_matrix[k,n] - const_Un_matrix[k,n]
                const_A_matrix[k,n] = const_A1_matrix[k,n] - const_A0_matrix[k,n]
        if load_ukln and not os.path.isfile('esq_ukln_consts_n%i.npz'%nstates):
            numpy.savez('esq_ukln_consts_n%i.npz'%nstates, u_kln=u_kln, const_R_matrix=const_R_matrix, const_A_matrix=const_A_matrix, const_q_matrix=const_q_matrix, const_q2_matrix=const_q2_matrix, const_unaffected_matrix=const_unaffected_matrix)
    #Sanity check
    for l in xrange(nstates):
        sanity_kln[:,l,:] = lamC12[l]*const_R_matrix + lamC6[l]*const_A_matrix + lamC1[l]*const_q_matrix + lamC1[l]**2*const_q2_matrix + const_unaffected_matrix
    del_kln = numpy.abs(u_kln - sanity_kln)
    print "Max Delta: %f" % numpy.max(del_kln)
    rel_del_kln = numpy.abs(del_kln/u_kln)
    #pdb.set_trace()
    ##################################################
    ############### END DATA INPUT ###################
    ##################################################
    #subsampling procedure, optional
    manual_subsample = False
    if manual_subsample:
        indicies_list = numpy.zeros([nstates,niterations], numpy.int32) #Maximum memory size
        N_k_sub = numpy.zeros([nstates], numpy.int32)
        for k in xrange(nstates):
            subsample = timeseries.subsampleCorrelatedData(u_kln[k,k,500:], verbose=False)
            N_k_sub[k] = len(subsample)
            indicies_list[k,:N_k_sub[k]] = subsample
            for l in xrange(nstates):
                u_kln[k,l,:N_k_sub[k]] = u_kln[k,l,subsample]
        Ntotal = N_k_sub.sum()
        print "Ntotal: = %i" % Ntotal
        mbar = MBAR(u_kln*kjpermolTokT, N_k_sub, verbose = True, method = 'adaptive')
        (DeltaF_ij, dDeltaF_ij) = mbar.getFreeEnergyDifferences(uncertainty_method='svd-ew')
        pdb.set_trace()
    #Create master uklns
    #Convert to dimless
    u_kln = u_kln * kjpermolTokT 
    const_R_matrix = const_R_matrix * kjpermolTokT 
    const_A_matrix = const_A_matrix * kjpermolTokT 
    const_unaffected_matrix = const_unaffected_matrix * kjpermolTokT
    const_q_matrix *= kjpermolTokT
    const_q2_matrix *= kjpermolTokT
    includeRef = False
    if includeRef:
        offset=1
    else:
        offset=0
    Nallstates = Nparm + nstates + offset #1 to recreate the refstate each time
    sig_range = (spacing(sigStartSpace**3,sigEndSpace**3,Nparm))**(1.0/3)
    epsi_range = spacing(epsiStartSpace,epsiEndSpace,Nparm)
    q_range = spacing(qStartSpace,qEndSpace,Nparm)
    epsi_plot_range = spacing(epsiStartSpace,epsi_max,Nparm)
    #Load subsequent f_ki
    f_ki_loaded = False
    state_counter = nstates
    while not f_ki_loaded and state_counter != 0:
        #Load the largest f_ki you can
        try:
            f_ki_load = numpy.load('esq_f_k_{myint:{width}}.npy'.format(myint=state_counter, width=len(str(state_counter))))
            f_ki_loaded = True
            f_ki_n = state_counter
        except:
            pass
        state_counter -= 1
    try:
        if nstates >= f_ki_n:
            draw_ki = f_ki_n
        else:
            draw_ki = nstates
        #Copy the loaded data
        f_ki = numpy.zeros(nstates)
        f_ki[:draw_ki] = f_ki_load[:draw_ki]
        #f_ki=numpy.array([0. ,61.20913184 ,71.40827393 ,75.87878531 ,78.40211785 ,79.89587372 ,80.45288761 ,80.28963586 ,79.71483901 ,78.90630752 ,77.90602495 ,0.5571373 ,64.03428624 ,20.01885445 ,-58.8966979 ,-178.11292884 ,-343.48493961 ,-556.63789832 ,70.70837529 ,30.71331917 ,-40.28879673 ,-144.71442394 ,-284.20819285 ,-460.07678445 ,-210.74990763 ,-202.3625391 ,-211.89582577 ,-217.2418002 ,-168.97823733 ,-158.94266495 ,-165.72416028 ,57.79253217 ,-195.03626708 ,-214.19139447 ,-196.65374506 ,-206.69571675 ,-270.11113276 ,-408.83567163 ,-147.95744809 ,-127.26705178 ,-192.96912003 ,-202.04056754 ,-196.08529618 ,-207.33238137 ,-155.20225707 ,-156.03612919 ,-91.06462805 ,3.81078618 ,-279.65874533])
        #comp = ncdata('complex', '.', u_kln_input=u_kln, nequil=0000, save_equil_data=True, manual_subsample=True, compute_mbar=True, verbose=True, mbar_f_ki=f_ki)
        comp = ncdata('complex', '.', u_kln_input=u_kln, nequil=0000, save_equil_data=True, subsample_method=subsample_method, compute_mbar=True, verbose=True, mbar_f_ki=f_ki)
    except:
        comp = ncdata('complex', '.', u_kln_input=u_kln, nequil=0000, save_equil_data=True, subsample_method=subsample_method, compute_mbar=True, verbose=True)
    if not f_ki_loaded or f_ki_n != nstates:
        numpy.save('esq_f_k_{myint:{width}}.npy'.format(myint=nstates, width=len(str(nstates))), comp.mbar.f_k)
    #(DeltaF_ij, dDeltaF_ij) = comp.mbar.getFreeEnergyDifferences(uncertainty_method='svd-ew')
    #printFreeEnergy(DeltaF_ij,dDeltaF_ij)
    #Reun from the subsampled data
    pdb.set_trace()
    maxN = comp.N_k.max()
    if comp.subsample_method == 'per-state':
        for k in xrange(nstates):
            ndxs = comp.retained_indices[k, :comp.N_k[k]]
            Nndxs = len(ndxs)
            u_kln[k,:,:Nndxs] = u_kln[k,:,ndxs].T
            const_R_matrix[k,:Nndxs] = const_R_matrix[k,ndxs].T
            const_A_matrix[k,:Nndxs] = const_A_matrix[k,ndxs].T
            const_unaffected_matrix[k,:Nndxs] = const_unaffected_matrix[k,ndxs].T
            const_q_matrix[k,:Nndxs] = const_q_matrix[k,ndxs].T
            const_q2_matrix[k,:Nndxs] = const_q2_matrix[k,ndxs].T
    else:
        u_kln = u_kln[:,:,comp.retained_indices]
        const_R_matrix = const_R_matrix[:,comp.retained_indices]
        const_A_matrix = const_A_matrix[:,comp.retained_indices]
        const_unaffected_matrix = const_unaffected_matrix[:,comp.retained_indices]
        const_q_matrix = const_q_matrix[:,comp.retained_indices]
        const_q2_matrix = const_q2_matrix[:,comp.retained_indices]
        niterations = len(comp.retained_indices)
    Ref_state = 6 #Reference state of sampling to pull from
    #if not (os.path.isfile('es_freeEnergies%s.npz'%spacename) and graphsfromfile) or not (os.path.isfile('es_%s/N%iRef%iOff%iEpsi%i.npz' % (spacename, Nparm, Ref_state, offset, Nparm-1)) and savedata): #nand gate
    pdb.set_trace()
    if not (os.path.isfile('es_freeEnergies%s.npz'%spacename) and graphsfromfile) or not (os.path.isfile('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, Nparm-1, Nparm-1)) and savedata) or timekln: #nand gate +timing flag
        #Create numpy arrys: q, epsi, sig
        DelF = numpy.zeros([Nparm, Nparm, Nparm])
        dDelF = numpy.zeros([Nparm, Nparm, Nparm])
        f_k = comp.mbar.f_k
        f_k_sub = numpy.zeros(Nallstates)
        f_k_sub[:nstates] = f_k
        N_k = comp.mbar.N_k
        N_k_sub = numpy.zeros(Nallstates, numpy.int32)
        N_k_sub[:nstates] = N_k
        #Populate energies
        run_start_time = time.time()
        number_of_iterations = Nparm**2
        iteration = 0
        #for iq in xrange(Nparm):
        #!!! 0-17, 17-34, 34-Nparm
        #!!! 0-25, 25-Nparm
        number_of_iterations = len(range(25,Nparm))*Nparm
        number_of_iterations = Nparm**2
        for iq in xrange(Nparm):
            #Grab charge
            q = q_range[iq]
            for iepsi in xrange(Nparm):
                initial_time = time.time()
                iteration += 1
                print "Q index: %i/%i --- Epsi index: %i/%i" % (iq, Nparm-1, iepsi, Nparm-1)
                #Save data files
                if not (os.path.isfile('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, iq, iepsi)) and savedata) or timekln: #nand gate + timing flag
                    epsi = epsi_range[iepsi]
                    #Create Sub matrix
                    u_kln_sub = numpy.zeros([Nallstates,Nallstates,niterations])
                    u_kln_sub[:nstates,:nstates,:] = u_kln
                    #Using PerturpedFreeEnergies instead of recreating the MBAR object every time. Saves time with same accuracy
                    #Perturbed assumes all l states are unsampled
                    u_kln_P = numpy.zeros([nstates,Nparm+offset,maxN]) 
                    #Rebuild the reference state
                    if includeRef:
                        Repsi = epsi_samp_space[Ref_state]
                        Rsig = sig_samp_space[Ref_state]
                        u_kln_sub[:nstates,nstates,:] = flamC12sqrt(Repsi,Rsig)*const_R_matrix + flamC6sqrt(Repsi,Rsig)*const_A_matrix + const_unaffected_matrix
                    for isig in xrange(Nparm):
                        sig = sig_range[isig]
                        u_kln_sub[:nstates,isig+nstates+offset,:] = flamC12sqrt(epsi,sig)*const_R_matrix + flamC6sqrt(epsi,sig)*const_A_matrix + flamC1(q)*const_q_matrix + flamC1(q)**2*const_q2_matrix + const_unaffected_matrix
                        #u_kln_P[:,isig+offset,:] = flamC12sqrt(epsi,sig)*const_R_matrix[:,:maxN] + flamC6sqrt(epsi,sig)*const_A_matrix[:,:maxN] + flamC1(q)*const_q_matrix[:,:maxN] + flamC1(q)**2*const_q2_matrix[:,:maxN] + const_unaffected_matrix[:,:maxN]
                    if not timekln:
                        mbar = MBAR(u_kln_sub, N_k_sub, initial_f_k=f_k_sub, verbose = False, method = 'adaptive')
                        (DeltaF_ij, dDeltaF_ij) = mbar.getFreeEnergyDifferences(uncertainty_method='svd-ew')
                        #(PDeltaF_ij, PdDeltaF_ij) = comp.mbar.computePerturbedFreeEnergies(u_kln_P, uncertainty_method='svd-ew')
                    if savedata and not timekln:
                        if not os.path.isdir('esq_%s' % spacename):
                            os.makedirs('esq_%s' % spacename) #Create folder
                        numpy.savez('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, iq, iepsi), DeltaF_ij=DeltaF_ij, dDeltaF_ij=dDeltaF_ij) #Save file
                else:
                    DeltaF_file = numpy.load('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, iq, iepsi))
                    #DeltaF_file = numpy.load('es_%s/N%iRef%iOff%iEpsi%i.npz' % (spacename, Nparm, Ref_state, offset, iepsi))
                    DeltaF_ij = DeltaF_file['DeltaF_ij']
                    dDeltaF_ij = DeltaF_file['dDeltaF_ij']
                #printFreeEnergy(DeltaF_ij, dDeltaF_ij)
                if not timekln:
                    if includeRef:
                        DelF[iq, iepsi,:] = DeltaF_ij[nstates,nstates+offset:]
                        dDelF[iq, iepsi,:] = dDeltaF_ij[nstates,nstates+offset:]
                    else:
                        DelF[iq, iepsi,:] = DeltaF_ij[Ref_state,nstates:]
                        dDelF[iq, iepsi,:] = dDeltaF_ij[Ref_state,nstates:]
                laptime = time.clock()
                # Show timing statistics. copied from Repex.py, copywrite John Chodera
                final_time = time.time()
                elapsed_time = final_time - initial_time
                estimated_time_remaining = (final_time - run_start_time) / (iteration) * (number_of_iterations - iteration)
                estimated_total_time = (final_time - run_start_time) / (iteration) * (number_of_iterations)
                estimated_finish_time = final_time + estimated_time_remaining
                print "Iteration took %.3f s." % elapsed_time
                print "Estimated completion in %s, at %s (consuming total wall clock time %s)." % (str(datetime.timedelta(seconds=estimated_time_remaining)), time.ctime(estimated_finish_time), str(datetime.timedelta(seconds=estimated_total_time)))
            numpy.savez('esq_freeEnergies%s.npz'%spacename, free_energy=DelF, dfree_energy=dDelF)
    else:
        #if os.path.isfile('es_%s/N%iRef%iOff%iEpsi%i.npz' % (spacename, Nparm, Ref_state, offset, Nparm-1)) and savedata: #Pull data from 
        if os.path.isfile('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, Nparm-1, Nparm-1)) and savedata: #Pull data from 
            DelF = numpy.zeros([Nparm, Nparm, Nparm])
            dDelF = numpy.zeros([Nparm, Nparm, Nparm])
            for iq in xrange(Nparm):
                for iepsi in xrange(Nparm):
                    #DeltaF_file = numpy.load('es_%s/N%iRef%iOff%iEpsi%i.npz' % (spacename, Nparm, Ref_state, offset, iepsi))
                    DeltaF_file = numpy.load('esq_%s/ns%iNp%iQ%iEpsi%i.npz' % (spacename, nstates, Nparm, iq, iepsi))
                    DeltaF_ij = DeltaF_file['DeltaF_ij']
                    dDeltaF_ij = DeltaF_file['dDeltaF_ij']
                    if includeRef:
                        DelF[iq, iepsi,:] = DeltaF_ij[nstates,nstates+1:]
                        dDelF[iq, iepsi,:] = dDeltaF_ij[nstates,nstates+1:]
                    else:
                        DelF[iq, iepsi,:] = DeltaF_ij[Ref_state,nstates:]
                        dDelF[iq, iepsi,:] = dDeltaF_ij[Ref_state,nstates:]
        else:
            figdata = numpy.load('esq_freeEnergies%s.npz'%spacename)
            DelF = figdata['free_energy']
            dDelF = figdata['dfree_energy']
    #pdb.set_trace()
    ###############################################
    ####### START SPECIFIC FREE ENERGY CALC #######
    ###############################################
    #Mapping is for UAmethane, NEoPentane, and C60 in that order
    realname = ['UAm', 'NOP', 'C60', 'LJ6', 'null', 'LJ11']
    nreal = len(realname)
    realepsi = numpy.array([1.2301, 3.4941, 1.0372, 0.7600, 0, 0.8])
    realsig  = numpy.array([0.3730, 0.6150, 0.9452, 1.0170, 0, 0.3])
    anrealepsi = numpy.array([1.2301, 3.4941, 1.0372, 0.7600])
    anrealsig  = numpy.array([0.3730, 0.6150, 0.9452, 1.0170])
    u_kln_sub = numpy.zeros([nstates+nreal,nstates+nreal,niterations])
    u_kln_sub[:nstates,:nstates,:] = u_kln
    f_k = comp.mbar.f_k
    f_k_sub = numpy.zeros(nstates+nreal)
    f_k_sub[:nstates] = f_k
    N_k = comp.mbar.N_k
    N_k_sub = numpy.zeros(nstates+nreal, numpy.int32)
    N_k_sub[:nstates] = N_k
    for imol in xrange(nreal):
        #Save data files
        epsi = realepsi[imol]
        sig = realsig[imol]
        #Create Sub matrix
        u_kln_sub[:nstates,imol+nstates+offset,:] = flamC12sqrt(epsi,sig)*const_R_matrix + flamC6sqrt(epsi,sig)*const_A_matrix + const_unaffected_matrix
    #mbar = MBAR(u_kln_sub, N_k_sub, initial_f_k=f_k_sub, verbose = False, method = 'adaptive')
    #(realDeltaF_ij, realdDeltaF_ij) = mbar.getFreeEnergyDifferences(uncertainty_method='svd-ew')
    #printFreeEnergy(realDeltaF_ij,realdDeltaF_ij)
    #for imol in xrange(nreal):
    #    print "Free energy of %s relative to LJ6: %.3f +- %.3f with %i states" % (realname[imol], realDeltaF_ij[Ref_state,nstates+imol], realdDeltaF_ij[Ref_state,nstates+imol], nstates)
    print realepsi
    print realsig
    ###############################################
    ######### END FREE ENERGY CALCULATIONS ########
    ###############################################
    #Set up a mask
    if masked:
        maDelF = ma.masked_where(numpy.fabs(DelF) > 200, DelF)
        madDelF = ma.masked_where(numpy.fabs(DelF) > 200, dDelF)
        orgDelF = DelF
        orgdDelF = dDelF
        DelF = maDelF
        dDelF = madDelF
    #Set up scaling
    C12_max = 3
    C12_min = 3E-5
    C6_max = 3
    C6_min = 1E-3
    plotC12_6 = True
    plotEpsiSig = True
    if plotC12_6 or plotEpsiSig:
        C12map = lambda x: ((C12_max - C12_min)*x + C12_min)*kjpermolTokcal
        C6map = lambda x: ((C6_max - C6_min)*x + C6_min)*kjpermolTokcal
        ylabel = r'$\epsilon$ in kcal/mol'
        if sig_factor != 3:
            xlabel = r'$\sigma$ in nm'
        else:
            xlabel = r'$\sigma^{%s}$ in nm$^{%s}$' % (sig_factor, sig_factor)
    else:
        C12map = lambda x: x
        C6map = lambda x: x
        xlabel = r'$\lambda$ of $C12_i$$'
        ylabel = r'$\lambda$ of $C6_i$$'
    lam_C12 = C12map(lam_range)
    lam_C6 = C6map(lam_range)
        
    DelF *= kjpermolTokcal/kjpermolTokT
    dDelF *= kjpermolTokcal/kjpermolTokT
    #Relative error
    reldDelF = numpy.abs(dDelF/DelF)
    pdb.set_trace()
 

    ################################################
    ################ region ID #####################
    ################################################
    '''
    This section will be used to identify where extra sampling should be done. optional flag set at the start of this section
    '''
    id_regions = False
    if id_regions:
        from scipy import ndimage
        err_threshold = 0.25 #kcal/mol
        #Filter data. notouch masks covers the sections we are not examining. touch is the sections we want
        mdDelF_notouch = ma.masked_less(dDelF, err_threshold)
        mdDelF_touch = ma.masked_greater(dDelF, err_threshold)
        #Extract the mask to get where there are features. We will use this to id features to operate on
        regions = ma.getmask(mdDelF_touch) #Extract the mask from the touch array as the Trues will line up with the areas more than the threshold
        #Create the features map of 1's where we want features (greater than threshold), zeroes otherwise
        features = numpy.zeros(dDelF.shape, dtype=numpy.int32)
        features[regions] = 1 #Define features
        #Define the features of the array by assigning labels
        test_struct = numpy.ones([3,3,3])
        feature_labels, num_features = ndimage.measurements.label(features)
        test_feature_labels, test_num_features = ndimage.measurements.label(features, structure=test_struct)
        """
        Important note:
        Labels of 0 in the feature_label arrays are not actually features! they are the background, so all looping will need to be done over the other indices
        """
        coms = numpy.zeros([num_features,3]) #Create the center of mass arrays
        maxes = numpy.zeros(coms.shape)
        maxes_esq = numpy.zeros(coms.shape)
        coms_esq = numpy.zeros(coms.shape) # q, epsi, and sig com
        test_coms = numpy.zeros([num_features,3]) #Create the center of mass arrays
        test_coms_esq = numpy.zeros(coms.shape) # q, epsi, and sig com
        for i in range(num_features):
           index = i + 1 #convert my counter to the feature index
           coms[i,:] = ndimage.measurements.center_of_mass(dDelF, feature_labels, index=index) #compute center of mass for each 
           test_coms[i,:] = ndimage.measurements.center_of_mass(dDelF, test_feature_labels, index=index) #compute center of mass for each 
           maxes[i,:] = ndimage.measurements.maximum_position(dDelF, feature_labels, index=index)
           #Compute the corrisponding q, epsi, and sig from each com
           fraction_along = coms[i,:] / Nparm
           test_fraction_along = test_coms[i,:] / Nparm
           coms_esq[i,0] = qStartSpace + (qEndSpace-qStartSpace)*fraction_along[0]
           coms_esq[i,1] = epsiStartSpace + (epsiEndSpace-epsiStartSpace)*fraction_along[1]
           coms_esq[i,2] = (sigStartSpace**3 + (sigEndSpace**3-sigStartSpace**3)*fraction_along[2])**(1.0/3)
           test_coms_esq[i,0] = qStartSpace + (qEndSpace-qStartSpace)*test_fraction_along[0]
           test_coms_esq[i,1] = epsiStartSpace + (epsiEndSpace-epsiStartSpace)*test_fraction_along[1]
           test_coms_esq[i,2] = sigStartSpace + (sigEndSpace-sigStartSpace)*test_fraction_along[2]
           maxes_esq[i,0] = q_range[maxes[i,0]]
           maxes_esq[i,1] = epsi_range[maxes[i,1]]
           maxes_esq[i,2] = sig_range[maxes[i,2]]
        print "Center of the %i regions with errors larger than %f kcal/mol" % (num_features, err_threshold)
        print "in units of  q, kJ/mol, and nm"
        print "Charge -- Epsilon -- Sigma"
        print coms_esq
        print "With test Structure"
        print test_coms_esq
        #Determine size of each feature to figure out which should have more
        resample_tol = 0.15
        #!!!
        #Convert to broader test structure
        num_features = test_num_features
        feature_labels = test_feature_labels
        resample_tol = 0.29
        #end!!!
        Nresample = numpy.ones(num_features, dtype=numpy.int32)
        Nsize = numpy.zeros(num_features, dtype=numpy.int32)
        for i in range(num_features):
            index = i + 1 #Convert to index
            Nsize[i] = numpy.where(feature_labels == index)[0].shape[0]
        #Nresample[Nsize == Nsize.max()] = 3
        Nresample[Nsize/float(Nsize.sum()) > resample_tol] = 3 #Resample at > 30% of the total points
        Nresamp_total = Nresample.sum()
        resamp_points = numpy.zeros([Nresample.sum(), 3])
        closest_interiors = numpy.zeros(resamp_points.shape)
        #Tesalate over where multiple samples are needed based on k-clustering Lloyd's algorithm
        pdb.set_trace()
        resamp_counter = 0
        for i in xrange(num_features):
            index = i + 1 #Convert to index
            if Nresample[i] > 1:
                feature_indices = numpy.transpose(numpy.array(numpy.where(feature_labels==index))) #Creates a NxD matrix where N=feature.size
                #feature_indices = numpy.where(feature_labels==i)
                mu, clusters = find_centers(feature_indices, Nresample[i], dDelF)
                for n in range(Nresample[i]):
                    fraction_along = mu[n] / Nparm
                    resamp_points[resamp_counter,0] = qStartSpace + (qEndSpace-qStartSpace)*fraction_along[0]
                    resamp_points[resamp_counter,1] = epsiStartSpace + (epsiEndSpace-epsiStartSpace)*fraction_along[1]
                    resamp_points[resamp_counter,2] = (sigStartSpace**3 + (sigEndSpace**3-sigStartSpace**3)*fraction_along[2])**(1.0/3)
                    resamp_counter += 1
                    closest_interiors = closest_index(mu[n], feature_labels, i)
            else:
                #Comment out to ignore these for weaker features
                resamp_points[resamp_counter,:] = coms_esq[i,:]
                resamp_counter += 1
                
        pdb.set_trace()
        #Test: set the dDelF where there are not features to 0
        #dDelF[ma.getmask(mdDelF_notouch)] = 0

    ################################################
    ################# PLOTTING #####################
    ################################################
    #Plot the sigma and epsilon free energies
    relativeErr = True
    if relativeErr:
        f,(Fplot,dFplot,rdFplot) = plt.subplots(3,1,sharex=True)
        rdFig = f
        plotlist=[Fplot,dFplot,rdFplot]
    else:
        f,(Fplot,dFplot) = plt.subplots(2,1,sharex=True)
        g,rdFplot = plt.subplots(1,1)
        rdFig = g
        plotlist=[Fplot,dFplot]
    '''
    Observant readers will notice that DelF and dDelF are in dimensions of [epsi,sig] but I plot in sig,epsi. That said, the color map is CORRECT with this method... somehow. I questioned it once and then decided to come back to it at a later date.
    '''
    import matplotlib.animation as ani
    cvmax = DelF.max()*1.01
    cvmin = DelF.min()*1.01
    #Set the default error tolerance
    try:
        errorlimits = numpy.load('n24_error_lims.npy')
        cdvmin = errorlimits[0]
        cdvmax = errorlimits[1]
    except:
        cdvmin = dDelF.min()*1.01
        cdvmax = dDelF.max()*1.01
        if nstates == 24:
            numpy.save('n24_error_lims.npy', numpy.array([dDelF.min()*1.01, dDelF.max()*1.01]))
    try:
        relerrlims = numpy.load('max_rel_err_lims.npy')
        crdvmin = relerrlims[0]
        crdvmax = relerrlims[1]
        #curmax = reldDelF.max()*1.01
        curmax = reldDelF.mean() + 2*numpy.sqrt(reldDelF.var())
        if curmax > crdvmax:
            print 'Max relative error exceeded, extending maximum to %f' % curmax
            numpy.save('max_rel_err_lims.npy', numpy.array([0,curmax]))
    except:
        crdvmin = 0
        #crdvmax = reldDelF.max()*1.01
        crdvmax = reldDelF.mean() + 2*numpy.sqrt(reldDelF.var())
        numpy.save('max_rel_err_lims.npy', numpy.array([0,crdvmax]))
    #imgFplot = Fplot.pcolormesh(sig_range**sig_factor,epsi_range,DelF[(Nparm-1)/2,:,:], vmax=cvmax, vmin=cvmin)
    imgFplot = Fplot.pcolormesh(sig_range**sig_factor,epsi_range,DelF[(Nparm-1)/2,:,:])
    #imgFplot = Fplot.pcolormesh(sig_range**sig_factor,epsi_range,[])
    #Set the colorbar
    divFplot = mal(Fplot)
    caxFplot = divFplot.append_axes('right', size='5%', pad=0.05)
    cFplot = f.colorbar(imgFplot, cax=caxFplot)
    #cFplot.set_clim(vmin=cvmin, vmax=cvmax)
    #set the minmax colorscales
    #print cFplot.get_clim()
    #cvmin, cvmax = (-21.971123537881027, 20.78176716595965) #These are the 11 nstate plots
    #cvmin, cvmax = (-14.542572154421956, 8.6595207877425739)
    ####### Error plot #######
    #imgdFplot = dFplot.pcolormesh(sig_range**sig_factor,epsi_range,dDelF[(Nparm-1)/2,:,:], vmax=cdvmax, vmin=cdvmin)
    imgdFplot = dFplot.pcolormesh(sig_range**sig_factor,epsi_range,dDelF[(Nparm-1)/2,:,:])
    #imgdFplot = dFplot.pcolormesh(sig_range**sig_factor,epsi_range,dDelF[5,:,:])
    #imgdFplot = dFplot.pcolormesh(sig_range**sig_factor,epsi_range,[])
    divdFplot = mal(dFplot)
    caxdFplot = divdFplot.append_axes('right', size='5%', pad=0.05)
    #Set the minmax colorscales
    #print imgdFplot.get_clim()
    #cdvmin, cdvmax = (0.00019094581786378227, 0.45022226894935008) #These are the 11 nstate plots
    #cdvmin, cdvmax = (3.1897634261829015e-05, 0.22292838017499619) 
    #sys.exit(0)
    imgdFplot.set_clim(vmin=cdvmin, vmax=cdvmax)
    cdFplot = f.colorbar(imgdFplot, cax=caxdFplot)
    ####### Relative Error Plot ########
    imgrdFplot = rdFplot.pcolormesh(sig_range**sig_factor,epsi_range,reldDelF[(Nparm-1)/2,:,:])
    divrdFplot = mal(rdFplot)
    caxrdFplot = divrdFplot.append_axes('right', size='5%', pad=0.05)
    imgrdFplot.set_clim(vmin=crdvmin, vmax=crdvmax)
    crdFplot = rdFig.colorbar(imgrdFplot, cax=caxrdFplot)

    sup_title_template = r'$\Delta G$ (top) and $\delta\Delta G$(bottom) with $q=%.2f$ for LJ Spheres' + '\n in units of kcal/mol'
    ftitle = f.suptitle('')
    #Set up the empty plots
    #Fscatters = []
    #dFscatters = []
    Fline, = Fplot.plot([], [], linewidth=2, color='k')
    dFline, = dFplot.plot([], [], linewidth=2, color='w')
    #F_scatter_noref = Fplot.scatter([], [], s=60, c='k', marker='x')
    #dF_scatter_noref = dFplot.scatter([], [], s=60, c='w', marker='x')
    #F_scatter_ref = Fplot.scatter([], [], s=70, c='k', marker='D')
    #dF_scatter_ref = dFplot.scatter([], [], s=70, c='w', marker='D')
    F_scatter_noref, = Fplot.plot([], [], linestyle='', markersize=5, color='k', marker='x', markeredgewidth=2)
    dF_scatter_noref, = dFplot.plot([], [], linestyle='', markersize=5, color='w', marker='x', markeredgewidth=2)
    F_scatter_ref, = Fplot.plot([], [], linestyle='', markersize=6, color='k', marker='D', markeredgewidth=2)
    dF_scatter_ref, = dFplot.plot([], [], linestyle='', markersize=6, color='w', marker='D', markeredgewidth=2, markeredgecolor='w')
    #Create the scatter sampled data
    noref = numpy.ma.array(range(nstates), mask=False)
    noref.mask[Ref_state]=True
    noref = noref.compressed()
    scatter_epsis = epsi_samp_space[noref]
    scatter_sig = sig_samp_space[noref]
    #for i in xrange(nstates):
    #    epsi = epsi_samp_space[i]
    #    sig = sig_samp_space[i]
    #    if i == Ref_state:
    #        marker_color = 'k'
    #        marker_size  = 70
    #        marker_style = 'D'
    #    else:
    #        marker_color = 'k'
    #        marker_size  = 60
    #        marker_style = 'x'
    #    #if lam == 0 and spacing is logspace:
    #    #    lam = 10**(StartSpace-1)
    #    Fplot.scatter(sig**sig_factor,epsi, s=marker_size, c=marker_color, marker=marker_style)
    #    dFplot.scatter(sig**sig_factor,epsi, s=marker_size, c='w', marker=marker_style)
    if plotReal and Ref_state == 6:
            Fplot.scatter(realsig**sig_factor, realepsi, s=60, c='k', marker='+')
            dFplot.scatter(realsig**sig_factor, realepsi, s=60, c='w', marker='+')
    #plotlam = sampled_lam
    #if spacing is logspace and plotlam[0] == 0 and not plotC12_6:
    #    plotlam[0] = 10**(StartSpace-1)
    #Fplot.plot(sig_range**sig_factor, epsi_plot_range, linewidth=2, color='k')
    #dFplot.plot(sig_range**sig_factor, epsi_plot_range, linewidth=2, color='w')
    if annotatefig:
        if plotReal:
            xyarrs = zip(anrealsig[:-1]**sig_factor, anrealepsi[:-1])
            antxt = "Chemically Realistic LJ Spheres"
            xoffset = 0.9
            realnamelong = ['UA Methane', 'Neopentane', r'C$_{60}$ Sphere']
            #Label the actual points
            bbox_def = dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7)
            Fplot.annotate(realnamelong[0], #String
                           (realsig[0], realepsi[0]), xycoords='data', #Point Where are we annotating at
                           xytext=(4, -18), textcoords='offset points', #Placement of text either absolute ('data') or relative ('offset points') to the xycoords
                           bbox=bbox_def) #style
            Fplot.annotate(realnamelong[1], #String
                           (realsig[1], realepsi[1]), xycoords='data', #Point Where are we annotating at
                           xytext=(-62, -20), textcoords='offset points', #Placement of text either absolute ('data') or relative ('offset points') to the xycoords
                           bbox=bbox_def) #style
            Fplot.annotate(realnamelong[2], #String
                           (realsig[2], realepsi[2]), xycoords='data', #Point Where are we annotating at
                           xytext=(6, 10), textcoords='offset points', #Placement of text either absolute ('data') or relative ('offset points') to the xycoords
                           bbox=bbox_def) #style
        else:
            xyarrs = [(anrealsig[-1]**sig_factor, anrealepsi[-1])]
            antxt = "Reference State"
            xoffset = 1
        my_annotate(Fplot,
                antxt,
                xy_arr=xyarrs, xycoords='data',
                xytext=(sig_range.max()/2*xoffset, epsiEndSpace/2), textcoords='data',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7),
                arrowprops=dict(arrowstyle="-|>",
                                connectionstyle="arc3,rad=0.2",
                                fc="w", linewidth=2))
        if nstates == 12:
            xypt = [(sig_samp_space[-1], epsi_samp_space[-1])]
            my_annotate(Fplot,
                        "Extra Sampling",
                        xy_arr=xypt, xycoords='data',
                        xytext=(sigPlotStart*1.05, epsiEndSpace/2*1.05), textcoords='data',
                        bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7),
                        arrowprops=dict(arrowstyle="-|>",
                                        connectionstyle="arc3,rad=0.2",
                                        fc="w", linewidth=2))
    for ax in plotlist:
        ax.set_yscale(spacename)
        ax.set_xscale(spacename)
        ax.set_ylim([epsiPlotStart,epsiPlotEnd])
        ax.set_xlim([sigPlotStart,sigPlotEnd])
        ax.patch.set_color('grey')
    f.subplots_adjust(hspace=0.02)
    f.text(0.05, .5, ylabel, rotation='vertical', horizontalalignment='center', verticalalignment='center', fontsize=20)
    if relativeErr:
        rdFplot.set_xlabel(xlabel, fontsize=20)
    else:
        dFplot.set_xlabel(xlabel, fontsize=20)
    #Animate the figures
    realcMax = -10**20 #Some really small number
    realcMin = 10**20 #some really large number
    realdcMax = -10**20 #Some really small number
    realdcMin = 10**20 #some really large number
    q_ref = q_samp_space[Ref_state]
    sig_ref = sig_samp_space[Ref_state]
    epsi_ref = epsi_samp_space[Ref_state]
    def cleanup():
        imgFplot.set_array([])
        imgdFplot.set_array([])
        imgrdFplot.set_array([])
        ftitle.set_text('')
        F_scatter_ref.set_data([], [])
        dF_scatter_ref.set_data([], [])
        F_scatter_noref.set_data([], [])
        dF_scatter_noref.set_data([], [])
        Fline.set_data([], [])
        dFline.set_data([], [])
        #for iscatter,discatter in zip(Fscatters,dFscatters):
        #    iscatter.set_data([],[])
        #    discatter.set_data([],[])
        if relativeErr:
            return imgFplot, imgdFplot, imgrdFplot, ftitle, F_scatter_noref, dF_scatter_noref, F_scatter_ref, dF_scatter_ref, Fline, dFline
        else:
            return imgFplot, imgdFplot, ftitle, F_scatter_noref, dF_scatter_noref, F_scatter_ref, dF_scatter_ref, Fline, dFline
    def moveq(qndx):
        q = q_range[qndx]
        #I have to create a secondary pcolormesh set since pcolormesh truncates the array size to make the render faster (I dont think pcolor would but would be slower)
        #If you don't do this, then it creates a weird set of lines which make no sense
        scrapFig, (scrapF, scrapdF, scraprdF) = plt.subplots(3,1)
        scrapFplot = scrapF.pcolormesh(sig_range**sig_factor,epsi_range,DelF[qndx,:,:])
        #Lock down the color choice for the error plot
        scrapdFplot = scrapdF.pcolormesh(sig_range**sig_factor,epsi_range,dDelF[qndx,:,:], vmax=cdvmax, vmin=cdvmin)
        #Lock down the color choice for the relative error plot
        scraprdFplot = scraprdF.pcolormesh(sig_range**sig_factor,epsi_range,reldDelF[qndx,:,:],vmax=crdvmax, vmin=crdvmin)
        #Reassign the plots, if you did not use an already generated array, you would need to .ravel() on the array you feed to set_array()
        imgFplot.set_array(scrapFplot.get_array())
        imgdFplot.set_array(scrapdFplot.get_array())
        imgrdFplot.set_array(scraprdFplot.get_array())
        ftitle.set_text(sup_title_template % q)
        Dmax = DelF[qndx,:,:].max()
        Dmin = DelF[qndx,:,:].min()
        dDmax = dDelF[qndx,:,:].max()
        dDmin = dDelF[qndx,:,:].min()
        imgFplot.set_clim(vmin=Dmin, vmax=Dmax)
        #imgdFplot.set_clim(vmin=dDmin, vmax=dDmax)
        #Set up the scatters
        #Set the Q scatters correctly
        qsampled = numpy.where(q_samp_space == q) #Get all sampled states from the current q value
        epsi_qsamp = epsi_samp_space[qsampled]
        sig_qsamp = sig_samp_space[qsampled]
        F_scatter_noref.set_data(sig_qsamp**sig_factor, epsi_qsamp)
        dF_scatter_noref.set_data(sig_qsamp**sig_factor, epsi_qsamp)
        if numpy.any(Ref_state == qsampled[0]):
            F_scatter_ref.set_data(sig_ref**sig_factor, epsi_ref)
            dF_scatter_ref.set_data(sig_ref**sig_factor, epsi_ref)
        else:
            #F_scatter_ref.set_data([], [])
            #dF_scatter_ref.set_data([], [])
            F_scatter_ref.set_data(sig_ref**sig_factor, epsi_ref)
            dF_scatter_ref.set_data(sig_ref**sig_factor, epsi_ref)
        if q == 0:
            Fline.set_data(sig_range**sig_factor, epsi_plot_range)
            dFline.set_data(sig_range**sig_factor, epsi_plot_range)
        else:
            Fline.set_data([], [])
            dFline.set_data([], [])
        #Cleanup scrap figure to avoid memory buildup
        plt.close(scrapFig)
        if relativeErr:
            return imgFplot, imgdFplot, imgrdFplot, ftitle, F_scatter_noref, dF_scatter_noref, F_scatter_ref, dF_scatter_ref, Fline, dFline
        else:
            return imgFplot, imgdFplot, ftitle, F_scatter_noref, dF_scatter_noref, F_scatter_ref, dF_scatter_ref, Fline, dFline
    aniU = ani.FuncAnimation(f, moveq, range(Nparm), interval=150, blit=False, init_func=cleanup)
    if relativeErr:
        filename='Animated_charging_rel{myint:{width}}.mp4'.format(myint=nstates, width=len(str(nstates)))
    else:
        filename='Animated_charging{myint:{width}}.mp4'.format(myint=nstates, width=len(str(nstates)))
    pdb.set_trace()
    aniU.save(filename, dpi=400)
    #save a single frame
    qframe=40
    moveq(qframe)
    f.savefig('DelF_Nstate_%i_Qndx_%i.png' % (nstates, qframe), bbox_inches='tight', dpi=400)
    if savefigs:
        if plotReal:
            plotrealstr = "T"
        else:
            plotrealstr = "F"
        f.patch.set_alpha(0.0)
        #f.savefig('LJ_GdG_ns%i_es%i_real%s_N%i_em%1.1f.png' % (nstates, sig_factor, plotrealstr, Nparm, epsiEndSpace), bbox_inches='tight', dpi=600)  
        print "Making the PDF, boss!"
        #f.savefig('LJ_GdG_ns%i_es%i_real%s_N%i_em%1.1f.pdf' % (nstates, sig_factor, plotrealstr, Nparm, epsiEndSpace), bbox_inches='tight')  
        #f.savefig('LJ_GdG_ns%i_es%i_real%s_N%i_em%1.1f.eps' % (nstates, sig_factor, plotrealstr, Nparm, epsiEndSpace), bbox_inches='tight')  
    else:
        plt.show()
    #pdb.set_trace()
    #sys.exit(0) #Terminate here
####################################################################################
####################################################################################
####################################################################################