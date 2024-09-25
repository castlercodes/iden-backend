
import random

def mod_exp(base, exp, mod):
    return pow(base, exp, mod)
p = 23 
g = 5 

def commitment_prover(g, p):
    r = random.randint(1, p - 2)
    T = mod_exp(g, r, p)
    return r, T

def challenge_verifier(q):
    c = random.randint(1, q - 1) 
    return c

def response_prover(r, c, H_f, p):
    s = (r + c * H_f) % (p - 1)
    return s

def verify_proof(g, s, T, C, c, p):
    left_hand_side = mod_exp(g, s, p)
    right_hand_side = (T * mod_exp(C, c, p)) % p
    return left_hand_side == right_hand_side

def schnorr_zkp_protocol(H_f):
    r, T = commitment_prover(H_f, g, p)
    print(f"Prover sends T = {T}")

    q = p - 1
    c = challenge_verifier(q)
    print(f"Verifier sends challenge c = {c}")

    s = response_prover(r, c, H_f, p)
    print(f"Prover sends response s = {s}")

    C = mod_exp(g, H_f, p)
    if verify_proof(g, s, T, C, c, p):
        print("Proof is valid.")
        return True
    else:
        print("Proof is invalid.")
        return False
