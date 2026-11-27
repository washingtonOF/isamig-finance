from resident_invoice_projection import RESIDENT_UNITS,payer_key

def inventory(db,auth):
    links={s.id:s.to_dict() for s in db.collection("unit_payer_links").stream()}
    residents={s.id:s.to_dict() for s in db.collection("residents").stream()}
    accounts={}
    for s in db.collection("users").stream():
        a=s.to_dict()
        if a.get("status")=="approved": accounts.setdefault(a.get("unit"),[]).append((s.id,a))
    for unit in sorted(RESIDENT_UNITS):
        reg=residents.get(unit,{})
        payer=payer_key(reg.get("cpf"))
        candidates=accounts.get(unit,[])
        if unit in ("401","501"): reason="shared_agreement_review"
        elif not payer or links.get(unit,{}).get("payer")!=payer: reason="missing_or_mismatched_link"
        elif sum(v.get("payer")==payer for v in links.values())!=1: reason="ambiguous_link"
        elif len(candidates)!=1: reason="missing_or_ambiguous_account"
        else:
            uid,a=candidates[0]
            user=auth.get_user(uid)
            if user.disabled or not user.email_verified or user.email!=a.get("email") or user.email!=reg.get("email"): reason="identity_review"
            elif a.get("role")!="resident": reason="administrative_review"
            else: reason="eligible_for_scope_review"
        print(unit,reason)
