import numpy as np
import proximal_func as pf
import opt_alg as alg

#from numba import jit
"""
iterative soft-thresholding
argmin ||Ax-b|||_2^2+(th/2)*||x||_1
matrix A input
"""
def IST_1( A, b, Nite, step, th ):
    #inverse operator
    invA = np.linalg.pinv(A)
    x_acc = step*(invA.dot(b))#np.zeros(x.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        x = pf.prox_l1_soft_thresh(x_acc,th)
        #residual
        r = A.dot(x) - b
        x_acc = x_acc - step*(invA.dot(r))
        print np.linalg.norm(r)
    return x

"""
iterative soft-thresholding
argmin ||A(x)-b|||_2^2+(th/2)*||x||_1
function A() input
"""
def IST_2( Afunc, invAfunc, b, Nite, step, th ):
    x_acc = step*invAfunc(b)#np.zeros(x.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        x = pf.prox_l1_soft_thresh2(x_acc, th)
        #residual
        r = Afunc(x) - b
        x_acc = x_acc - step*invAfunc(r)
        print np.linalg.norm(r)
    return x

def IST_22( Afunc, invAAfunc, invAfunc, b, Nite, step, th ):
    invAb = invAfunc(b)
    x_acc = step*invAb#np.zeros(x.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        x = pf.prox_l1_soft_thresh2(x_acc, th)
        #residual
        r = invAAfunc(x) - invAb      
        x_acc = x_acc - step*r
        print np.linalg.norm(r)
    return x

"""
iterative soft-thresholding
argmin ||A(x)-b|||_2^2+(th/2)*||Tfunc(x)||_1
function A() input
Tfunc can be wavelet, singular values of Hankel etc.
proximal gradient method which is
x^k = prox_tkh(x^k-1 - tk * grad(x^k-1))
"""
def IST_3( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, th ):
    x_acc = step*invAfunc(b) #np.zeros(x.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        x = pf.prox_l1_Tf_soft_thresh2(Tfunc,invTfunc,x_acc, th)
        #residual
        r = Afunc(x) - b
        x_acc = x_acc - step*invAfunc(r)
        print np.linalg.norm(r)
    return x

def IST_32( Afunc, invAAfunc, invAfunc, Tfunc, invTfunc, b, Nite, step, th ):
    invAb = invAfunc(b)
    x_acc = step*invAb #np.zeros(x.shape)
    # iteration
    for _ in range(Nite):
        # soft threshol
        x = pf.prox_l1_Tf_soft_thresh2(Tfunc,invTfunc,x_acc, th)
        #residual
        r = invAAfunc(x) - invAb
        x_acc = x_acc - step*r
        print np.linalg.norm(r)
    return x

# wrap of several IST function
def IST_wrap ( Aopt, Topt = None, b = None, Nite = None, step = None, th = None ):
    if b is None:
        print('FIST donot has input data!')
        return 
    if Nite is None:
        Nite = 20 #number of iterations
    if step is None:
        step = 0.1 #step size
    if th is None:
        th = 0.04 # theshold level

    if Topt is not None:#||Ax - b||_2 + ||Tx||_1
        if "forward_backward" in dir(Aopt):
            x = IST_32( Aopt.forward, Aopt.forward_backward, Aopt.backward, Topt.backward, Topt.forward, b, Nite, step, th )
        else:
            x = IST_3 ( Aopt.forward,          Aopt.backward, Topt.backward, Topt.forward, b, Nite, step, th )
    else: #||Ax - b||_2 + ||x||_1
        if "forward_backward" in dir(Aopt):
            x = IST_22( Aopt.forward, Aopt.forward_backward, Aopt.backward, b, Nite, step, th )
        else:
            x = IST_2 ( Aopt.forward,          Aopt.backward, b, Nite, step, th )       
    return x
"""
fast iterative soft-thresholding
argmin ||A(x)-b|||_2^2+(th/2)*||Tfunc(x)||_1
function A() input
Tfunc can be wavelet, singular values of Hankel etc.
proximal gradient method which is
y^0 = x^0
x^k = prox_tkh(y^k-1 - tk * grad(y^k-1))
y^k = x^k + (k-1)/(k+2) (x^k - x^k-1)
""" 
"""
def FIST_3( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, th ):
    y     = step*invAfunc(b) #np.zeros(x.shape)
    y_acc = np.zeros(y.shape,dtype=b.dtype)
    x_pre = y
    k     = 1
    # iteration
    for _ in range(Nite):
        #residual
        r = Afunc(y) - b
        y_acc = y_acc - step*invAfunc(r)
        # soft threshold
        x = pf.prox_l1_Tf_soft_thresh2(Tfunc,invTfunc,y_acc, th)        
        y = x + np.multiply((k-1)/(k+2), (x - x_pre))
        x_pre = x
        k += 1
        print np.linalg.norm(r)
    return x
"""
"""
fast iterative soft-thresholding
argmin ||A(x)-b|||_2^2+(th/2)*||Tfunc(x)||_1
function A() input
Tfunc can be wavelet, singular values of Hankel etc.
proximal gradient method which is
y^0 = x^0
x^k = prox_tkh(y^k-1 - tk * grad(y^k-1))
t^(k+1) = (1+(1+4*t^k^2)^0.5)/2
y^k = x^k + (t^k-1)/(t^(k+1)) (x^k - x^k-1)
""" 
def FIST_2( Afunc, invAfunc, b, Nite, step, th ):
    y     = step*invAfunc(b) #np.zeros(x.shape)
    y_acc = np.zeros(y.shape,dtype=b.dtype)
    x_pre = y
    t     = np.ones(Nite+1)
    # iteration
    for k in range(Nite):
        #residual
        r      = Afunc(y) - b
        y_acc  = y_acc - step*invAfunc(r)
        # soft threshold
        x      = pf.prox_l1_soft_thresh2(y_acc, th)
        t[k+1] = (1+(1+4*t[k]**2)**0.5)/2   
        y      = x + np.multiply((t[k]-1)/(t[k+1]), (x - x_pre))
        x_pre  = x
        print np.linalg.norm(r)
    return x

def FIST_22( Afunc, invAAfunc, invAfunc, b, Nite, step, th ):
    invAb = invAfunc(b) #np.zeros(x.shape)
    y     = step*invAb
    y_acc = np.zeros(y.shape,dtype=b.dtype)
    x_pre = y
    t     = np.ones(Nite+1)
    # iteration
    for k in range(Nite):
        #residual
        r      = invAAfunc(y) - invAb
        y_acc  = y_acc - step*r
        # soft threshold
        x      = pf.prox_l1_soft_thresh2(y_acc, th)   
        t[k+1] = (1+(1+4*t[k]**2)**0.5)/2   
        y      = x + np.multiply((t[k]-1)/(t[k+1]), (x - x_pre))
        x_pre  = x
        print np.linalg.norm(r)
    return x


def FIST_3( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, th ):
    y     = step*invAfunc(b) #np.zeros(x.shape)
    y_acc = np.zeros(y.shape,dtype=b.dtype)
    x_pre = y
    t     = np.ones(Nite+1)
    # iteration
    for k in range(Nite):
        #residual
        r      = Afunc(y) - b
        y_acc  = y_acc - step*invAfunc(r)
        # soft threshold
        x      = pf.prox_l1_Tf_soft_thresh2(Tfunc,invTfunc,y_acc, th)    
        t[k+1] = (1+(1+4*t[k]**2)**0.5)/2   
        y      = x + np.multiply((t[k]-1)/(t[k+1]), (x - x_pre))
        x_pre  = x
        print np.linalg.norm(r)
    return x

def FIST_32( Afunc, invAAfunc, invAfunc, Tfunc, invTfunc, b, Nite, step, th ):
    invAb = invAfunc(b) #np.zeros(x.shape)
    y     = step*invAb
    y_acc = np.zeros(y.shape,dtype=b.dtype)
    x_pre = y
    t     = np.ones(Nite+1)
    # iteration
    for k in range(Nite):
        #residual
        r      = invAAfunc(y) - invAb
        y_acc  = y_acc - step*r
        # soft threshold
        x      = pf.prox_l1_Tf_soft_thresh2(Tfunc,invTfunc,y_acc, th)    
        t[k+1] = (1+(1+4*t[k]**2)**0.5)/2   
        y      = x + np.multiply((t[k]-1)/(t[k+1]), (x - x_pre))
        x_pre  = x
        print np.linalg.norm(r)
    return x

# wrap of several FIST function
def FIST_wrap ( Aopt, Topt = None, b = None, Nite = None, step = None, th = None ):
    if b is None:
        print('FIST donot has input data!')
        return 
    if Nite is None:
        Nite = 20 #number of iterations
    if step is None:
        step = 0.1 #step size
    if th is None:
        th = 0.04 # theshold level
    if Topt is not None:#||Ax - b||_2 + ||Tx||_1
        if "forward_backward" in dir(Aopt):
            x = FIST_32( Aopt.forward, Aopt.forward_backward, Aopt.backward, Topt.backward, Topt.forward, b, Nite, step, th )
        else:
            x = FIST_3 ( Aopt.forward,          Aopt.backward, Topt.backward, Topt.forward, b, Nite, step, th )
    else: #||Ax - b||_2 + ||x||_1
        if "forward_backward" in dir(Aopt):
            x = FIST_22( Aopt.forward, Aopt.forward_backward, Aopt.backward, b, Nite, step, th )
        else:
            x = FIST_2 ( Aopt.forward,          Aopt.backward, b, Nite, step, th )       
    return x
"""
ADMM for argmin ||Ax-b|||_2^2+lambda*||x||_1
Lagrangian is L(x,z,y) = f(x) + g(z) + y^H(x-z) + (rho/2)*||x-z||_2^2
for f(x) = ||Ax-b|||_2^2
and g(z) = lambda*||z||_1,
so that L(x,z,u) = f(x) + g(z) + (rho/2)*||x-z+y/rho||_2^2 + const,
and u = y/rho

duality is duality(y) = inf_x,z L(x,z,y)
dual problem is  max duality(y) <= f0+g0 (which is the minimal value of orginal cost function f(x) + g(z))
gradient of duality is grad_dual(y) = x-z
gradient mehtod for dual problem (maximizing dual) is u^k+1 = u^k + alphi*(x^k-z^k), alphi is step size

dual ascent method is
x^k+1 = argmin_x L(x,z^k,u^k) = argmin_x [ f(x) + (rho/2)*||x-z^k+u^k||_2^2 ] = argmin_x [ ||Ax-b|||_2^2 + (rho/2)*||x-z^k+u^k||_2^2 ]
z^k+1 = argmin_z L(x^k,z,u^k) = argmin_z [ g(z) + (rho/2)*||x^k-z+u^k||_2^2 ] = argmin_z [ lambda*||z||_1 + (rho/2)*||x^k-z+u^k||_2^2 ]
u^k+1 = u^k + alphi*(x^k-z^k)

using proximal functions
x^k+1 = prox_l2_Axnb(A,b,x0=z^k-u^k,rho)
z^k+1 = prox_l1_soft_thresh(x0=x^k+u^k,th = lambda/rho)
u^k+1 = u^k + alphi*(x^k+1-z^k+1)
"""
def ADMM_l2Axnb_l1x_1( A, b, Nite, step, l1_r, rho ):
    z = np.pinv(A).dot(b)
    u = np.zeros(z.shape)
    # iteration
    for _ in range(Nite):
        # soft threshol
        x = pf.prox_l2_Axnb(A,b,z-u,rho)
        z = pf.prox_l1_soft_thresh(x+u,l1_r/rho)
        u = u + step*(x-z)
        print np.linalg.norm(x-z)
    return x
"""
faster version with percalculation
"""
def ADMM_l2Axnb_l1x_2( A, b, Nite, step, l1_r, rho ):
    z = np.pinv(A).dot(b)
    u = np.zeros(z.shape)
    Q_dot, A_T_b = prox_l2_Axnb_precomputpart( A, b, rho )
    # iteration
    for _ in range(Nite):
        # soft threshold
        x = Q_dot(A_T_b + rho*(z-u)) #prox_l2_Axnb_iterpart( Q_dot, A_T_b, z-u, rho )
        z = pf.prox_l1_soft_thresh(x+u,l1_r/rho)
        u = u + step*(x-z)
        print np.linalg.norm(x-z)
    return x

"""
ADMM for argmin ||Afunc(x)-b|||_2^2+lambda*||x||_1
Lagrangian is L(x,z,y) = f(x) + g(z) + y^H(x-z) + (rho/2)*||x-z||_2^2
for f(x) = ||Afunc(x)-b|||_2^2
and g(z) = lambda*||z||_1,
so that L(x,z,u) = f(x) + g(z) + (rho/2)*||x-z+y/rho||_2^2 + const,
and u = y/rho

duality is duality(y) = inf_x,z L(x,z,y)
dual problem is  max duality(y) <= f0+g0 (which is the minimal value of orginal cost function f(x) + g(z))
gradient of duality is grad_dual(y) = x-z
gradient mehtod for dual problem (maximizing dual) is u^k+1 = u^k + alphi*(x^k-z^k), alphi is step size

dual ascent method is
x^k+1 = argmin_x L(x,z^k,u^k) = argmin_x [ f(x) + (rho/2)*||x-z^k+u^k||_2^2 ] = argmin_x [ ||Afunc(x)-b|||_2^2 + (rho/2)*||x-z^k+u^k||_2^2 ]
z^k+1 = argmin_z L(x^k,z,u^k) = argmin_z [ g(z) + (rho/2)*||x^k-z+u^k||_2^2 ] = argmin_z [ lambda*||z||_1 + (rho/2)*||x^k-z+u^k||_2^2 ]
u^k+1 = u^k + alphi*(x^k-z^k)

using proximal functions
x^k+1 = prox_l2_Afxnb_GD(Afunc, invAfunc, b, x0=z^k-u^k, rho, Nite=100, step=0.01 )
z^k+1 = prox_l1_soft_thresh(x0=x^k+u^k,th = lambda/rho)
u^k+1 = u^k + alphi*(x^k+1-z^k+1)
"""
def ADMM_l2Afxnb_l1x( Afunc, invAfunc, b, Nite, step, l1_r, rho, cgd_Nite = 3 ):
    z = invAfunc(b) #np.zeros(x.shape)
    u = np.zeros(z.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        #x = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u,rho,10,0.1)
        x = pf.prox_l2_Afxnb_CGD( Afunc, invAfunc, b, z-u, rho, cgd_Nite )
        z = pf.prox_l1_soft_thresh(x+u,l1_r/rho)
        u = u + step*(x-z)
        print np.linalg.norm(x-z)
    return x

#tv minimization
#tv_r, regularization parameter for tv term
def ADMM_l2Afxnb_tvx( Afunc, invAfunc, b, Nite, step, tv_r, rho, cgd_Nite = 3, tvndim = 2 ):
    z = invAfunc(b) #np.zeros(x.shape), z=AH(b)
    u = np.zeros(z.shape)
    # 2d or 3d, use different proximal funcitons
    if tvndim is 2:
        tvprox = pf.prox_tv2d_r
    elif tvndim is 3:
        tvprox = pf.prox_tv3d
    else:
        print('dimension imcompatiable in ADMM_l2Afxnb_tvx')
        return None
    # iteration
    for _ in range(Nite):
        # soft threshold
        #x = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u,rho,20,0.1)
        x = pf.prox_l2_Afxnb_CGD( Afunc, invAfunc, b, z-u, rho, cgd_Nite )
        z = tvprox(x + u, 2.0 * tv_r/rho)#pf.prox_tv2d(x+u,2*tv_r/rho)
        u = u + step * (x - z)
        print( 'gradient in ADMM %g' % np.linalg.norm(x-z))
    return x

#tv minimization
#tv_r, regularization parameter for tv term
def ADMM_l2Afxnb_tvTfx( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, tv_r, rho, cgd_Nite = 3, tvndim = 2 ):
    z = invAfunc(b) #np.zeros(x.shape), z=AH(b)
    u = np.zeros(z.shape)
    # 2d or 3d, use different proximal funcitons
    if tvndim is 2:
        tvprox = pf.prox_tv2d_r
    elif tvndim is 3:
        tvprox = pf.prox_tv3d
    else:
        print('dimension imcompatiable in ADMM_l2Afxnb_tvx')
        return None
    # iteration
    for _ in range(Nite):
        # soft threshold
        #x = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u,rho,20,0.1)
        x = pf.prox_l2_Afxnb_CGD( Afunc, invAfunc, b, z-u, rho, cgd_Nite )
        z = invTfunc(tvprox(Tfunc(x + u), 2.0 * tv_r/rho))#pf.prox_tv2d(x+u,2*tv_r/rho)
        u = u + step * (x - z)
        print( 'gradient in ADMM %g' % np.linalg.norm(x-z))
    return x

#l1 with tranform function Tf, which can be wavelet transform
def ADMM_l2Afxnb_l1Tfx( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, l1_r, rho, cgd_Nite = 3 ):
    z = invAfunc(b)#np.zeros(x.shape)
    u = np.zeros(z.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        #x = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u,rho,10,0.1)
        x = pf.prox_l2_Afxnb_CGD( Afunc, invAfunc, b, z-u, rho, cgd_Nite )        
        z = pf.prox_l1_Tf_soft_thresh(Tfunc,invTfunc,x+u,l1_r/rho)
        u = u + step*(x-z)
        print( 'gradient in ADMM %g' % np.linalg.norm(x-z))
    return x

"""
ADMM for argmin ||Afunc(x_1)-b|||_2^2+lambda1*||x_2||_1 + lambda2*||Tfunc(x_3)||_1
Lagrangian is L(x,z,y) = f_1(x_1) + f_2(x_2) + f_3(x_3) + g(z) + sum_i=1,2,3_[y^H(x_i-z) + (rho/2)*||x_i-z||_2^2 ]
for f_1(x_1) = ||Afunc(x_1)-b||_2^2, f_2(x_2) = lambda1*||x_2||_1, f_3(x_3) = lambda2*||Tfunc(x_3)||_1 and g(z) = 0

so that L(x_i,z,u) = sum_i=1,2,3_( f_i(x_i) + (rho/2)*||x_i-z+u_i||_2^2 ) + const, and u_i = y_i/rho

gradient mehtod for dual problem (maximizing dual) is u_i^k+1 = u_i^k + alphi*(x_i^k-z^k), alphi is step size

dual ascent method is
x_i^k+1 = argmin_x_i L(x_i,z^k,u^k) = argmin_x_i [ f_i(x_i) + (rho/2)*||x_i-z^k+u_i^k||_2^2 ]
=>x_1^k+1 = argmin_x_1 [ ||Afunc(x_1)-b||_2^2     + (rho/2)*||x_1-z^k+u_1^k||_2^2 ]
=>x_2^k+1 = argmin_x_2 [ lambda1*||x_2||_1        + (rho/2)*||x_2-z^k+u_2^k||_2^2 ]
=>x_3^k+1 = argmin_x_3 [ lambda2*||Tfunc(x_3)||_1 + (rho/2)*||x_3-z^k+u_2^k||_2^2 ]
z^k+1 = argmin_z L(x^k,z,u^k) = argmin_z [(rho/2)*||x^k-z+u^k||_2^2 ]
=> z^k+1 = average(x_i^k + u_i^k)
u_i^k+1 = u_i^k + alphi*(x_i^k-z^k)

using proximal functions
x_1^k+1 = prox_l2_Afxnb_GD(Afunc, invAfunc, b,  x0=z^k-u_1^k, rho, Nite=100, step=0.01 )
x_2^k+1 = prox_l1_soft_thresh   (               x0=z^k-u_2^k,th = lambda1/rho)
x_3^k+1 = prox_l1_Tf_soft_thresh(Tfunc,invTfunc,x0=z^k-u_3^k,th = lambda2/rho)
z^k+1 = average(x_i^k)
u_i^k+1 = u_i^k + alphi*(x_i^k+1-z^k+1)
"""
def ADMM_l2Afxnb_l1x_l1Tfx( Afunc, invAfunc, Tfunc, invTfunc, b, Nite, step, l1_r1, L1_r2, rho ):
    z = invAfunc(b)
    u1 = np.zeros(z.shape)
    u2 = np.zeros(z.shape)
    u3 = np.zeros(z.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        x1 = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u1,rho,10,0.1)
        x2 = pf.prox_l1_soft_thresh(z-u2,l1_r1/rho)
        x3 = pf.prox_l1_Tf_soft_thresh(Tfunc,invTfunc,z-u3,l1_r2/rho)
        z = (x1 + x2 + x3)/3 + (u1 + u2 + u3)/3
        u1 = u1 + step*(x1-z)
        u2 = u2 + step*(x2-z)
        u3 = u3 + step*(x3-z)
        print np.linalg.norm(x1-z)
    return x1

def ADMM_l2Afxnb_l1x_2( Afunc, invAfunc, b, Nite, step, l1_r1, rho, cgd_Nite = 3 ):
    z = invAfunc(b)
    u1 = np.zeros(z.shape)
    u2 = np.zeros(z.shape)
    # iteration
    for _ in range(Nite):
        # soft threshold
        #x1 = pf.prox_l2_Afxnb_GD(Afunc,invAfunc,b,z-u1,rho,10,0.1)
        x1 = pf.prox_l2_Afxnb_CGD( Afunc, invAfunc, b, z-u1, rho, cgd_Nite )
        x2 = pf.prox_l1_soft_thresh(z-u2,l1_r1/rho)
        z = (x1 + x2)/2.0 + (u1 + u2)/2.0
        u1 = u1 + step*(x1-z)
        u2 = u2 + step*(x2-z)
        print np.linalg.norm(x2-x1)
    return x1
