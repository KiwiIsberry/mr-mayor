import random, statistics as st, sys
N=7; ROAD=3
LOTS=[(r,c) for r in range(N) for c in range(N) if r!=ROAD and c!=ROAD]
def zone(r,c): return None if r==ROAD or c==ROAD else ('old' if c<3 else 'river') if r<3 else ('soft' if c<3 else 'open')
HAZ={'flood':(('house','shop'),('river','river','soft')),'quake':(('condo','factory'),('soft','soft','open')),
     'storm':(('house','factory'),('open','open','old')),'fire':(('shop','condo'),('old','old','river'))}
PRICE=dict(house=4,shop=7,factory=8,condo=10,green=4); INC=dict(house=1,shop=2,factory=4,condo=1)
SIZE=dict(factory=2,condo=2)
STAR=dict(income=(22,36),housing=(14,24),green=(3,6),totems=(2,4))
EV=[('tourism',3),('investor',2),('grant',2),('tax',2),('wastewater',2),('road',3),('power',1),('forecast',3),('drill',2),('volunteers',2),
    ('material',2),('totemsale',2),('movein',1),('strike',1),('holiday',1),('tide',1),('parkdemand',1),('quiet',2)]
class P:
    def __init__(s,t,cells): s.t=t; s.cells=cells; s.d=False; s.rf=False
class G:
    def __init__(s,cfg,pol,rng):
        s.c=cfg; s.pol=pol; s.r=rng; s.coins=6; s.p=[]; s.tot=set(); s.ff=0; s.ev=[]; s.ds=[]
        for t,cell in [('house',(0,0)),('house',(1,1)),('shop',(0,2)),('green',(1,0))]: s.p.append(P(t,[cell]))
        s.hits=0; s.dis=0; s.blocked=0; s.bought=0
    def occ(s): return {c for p in s.p for c in p.cells}
    def n(s,t,ok=False): return sum(1 for p in s.p if p.t==t and (not ok or not p.d))
    def income(s,m={}): return sum(INC.get(p.t,0) for p in s.p if not p.d and not (m.get('noshop') and p.t=='shop') and not (m.get('nofac') and p.t=='factory'))
    def housing(s): return s.n('house',1)+4*s.n('condo',1)
    def year(s): return (s.round-1)//3+1
    def risk(s,m): return min(12,s.c['r0']+2*(s.year()-1)+s.n('factory')+m.get('tide',0))
    def tprice(s,m): return max(0,s.c['tp'][len(s.tot)] if s.c.get('esc') else 8)-m.get('tdisc',0)
    def refill(s):
        s.ds=[(k,z) for k,(h,zs) in HAZ.items() for z in zs]+[('ffire',None)]*s.ff; s.r.shuffle(s.ds)
    def cellsfor(s,t,r,c,o): return [(r,c),(r,c+1)] if t in SIZE and o=='h' else [(r,c),(r+1,c)] if t in SIZE else [(r,c)]
    def ok(s,t,cells,oc):
        for (a,b) in cells:
            if not(0<=a<N and 0<=b<N) or zone(a,b) is None or (a,b) in oc: return False
        if t in ('shop','factory'):
            homes={c for p in s.p if p.t in('house','condo') for c in p.cells}
            if not any((a+da,b+db) in homes for (a,b) in cells for da,db in((1,0),(-1,0),(0,1),(0,-1))): return False
        return True
    def threat(s,t,z):
        return sum(zs.count(z) for k,(h,zs) in HAZ.items() if t in h and k not in s.tot)
    def spots(s,t):
        oc=s.occ(); out=[]
        for (r,c) in LOTS:
            for o in (('h','v') if t in SIZE else ('h',)):
                cl=s.cellsfor(t,r,c,o)
                if s.ok(t,cl,oc): out.append(cl)
        return out
    def build(s,t,m,free=False):
        sp=s.spots(t)
        if not sp: return False
        cost=0 if free else PRICE[t]+m.get('mat',0)
        if s.coins<cost: return False
        if s.pol.startswith('planner'):
            def score(cl):
                th=s.threat(t,zone(*cl[0]))*3
                if t!='factory': th+=sum(1 for p in s.p if p.t=='factory' for a in cl for b in p.cells if abs(a[0]-b[0])+abs(a[1]-b[1])==1)*2
                return th+s.r.random()
            cl=min(sp,key=score) if s.pol=='planner' else s.r.choice(sp)
        else: cl=s.r.choice(sp)
        s.coins-=cost; s.p.append(P(t,cl))
        if t=='factory':
            s.ff+=1
            if s.ds: s.ds.insert(s.r.randrange(len(s.ds)+1),('ffire',None))
        return True
    def stars(s):
        v=dict(income=s.income(),housing=s.housing(),green=s.n('green'),totems=len(s.tot))
        return sum(2 if v[k]>=b else 1 if v[k]>=a else 0 for k,(a,b) in STAR.items())
    def disaster(s,card):
        k,z=card; s.dis+=1
        key='fire' if k=='ffire' else k
        if key in s.tot: s.blocked+=1; return
        if k=='ffire':
            fs=[p for p in s.p if p.t=='factory']
            if not fs: return
            f=s.r.choice(fs)
            tg=[p for p in s.p if p is f or (p.t!='green' and any(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a in p.cells for b in f.cells))]
        else:
            h,_=HAZ[k]; tg=[p for p in s.p if p.t in h and zone(*p.cells[0])==z]
        for p in tg:
            if p.d: continue
            if p.rf: p.rf=False; continue
            p.d=True; s.hits+=1
    def manage(s,m):
        pol=s.pol; yr=s.year()
        # repairs
        free=m.get('vol',0)
        for p in sorted([p for p in s.p if p.d],key=lambda p:-INC.get(p.t,0)):
            if free: p.d=False; free-=1; continue
            if s.coins>=PRICE[p.t] and (pol!='casual' or s.r.random()<.5): s.coins-=PRICE[p.t]; p.d=False
        if m.get('free_house'): s.build('house',m,free=True)
        # totems
        if pol.startswith('planner'):
            want = (s.round>=s.c['tot_from'])
            while want and len(s.tot)<4:
                exp={k:sum(1 for p in s.p if p.t in HAZ[k][0] and zone(*p.cells[0]) in HAZ[k][1])+(s.n('factory') if k=='fire' else 0) for k in HAZ if k not in s.tot}
                k=max(exp,key=exp.get); pr=s.tprice(m)
                if s.coins>=pr+(0 if s.round>=10 else 4) and (exp[k]>0 or s.round>=9): s.coins-=pr; s.tot.add(k); s.bought+=1
                else: break
        elif pol=='novice':
            if s.round>=8:
                for k in s.r.sample(list(HAZ),4):
                    if k not in s.tot and s.coins>=s.tprice(m)+2: s.coins-=s.tprice(m); s.tot.add(k)
        elif pol=='hoarder':  # farm money, then buy every Totem at once
            if s.round>=s.c['hoard_at']:
                for k in HAZ:
                    if k not in s.tot and s.coins>=s.tprice(m): s.coins-=s.tprice(m); s.tot.add(k)
        # build towards stars
        econ = s.round<=s.c.get('econ_until',7) and pol in ('planner','planner_rand','hoarder')
        for _ in range(14):
            inc,hs,gr=s.income(),s.housing(),s.n('green')
            reserve=0 if s.round>=11 else (2 if pol.startswith('planner') else 0)
            mat=m.get('mat',0)
            if econ:
                order=['factory','shop','house'] if inc<36 else ['condo','house','green']
            else:
                order=[]
                if hs<24: order.append('condo' if s.coins>=10+mat else 'house')
                if gr<6: order.append('green')
                if inc<36: order+=['factory','shop']
                if hs<24: order.append('house')
            if pol in('novice','casual'): s.r.shuffle(order)
            if pol=='casual' and s.r.random()<.4: break
            done=False
            for t in order:
                if s.coins-reserve>=PRICE[t]+mat and s.build(t,m): done=True; break
            if not done: break
    def play(s):
        for s.round in range(1,13):
            m={}; noroll=False
            for _ in range(2):
                if not s.ev: s.ev=[k for k,n in EV for _ in range(n)]; s.r.shuffle(s.ev)
                k=s.ev.pop(); f=s.n('factory'); d=0
                if k=='tourism': d=s.n('shop',1)
                elif k=='investor': d=2+s.n('factory',1) if f else 0
                elif k=='grant': d=4
                elif k=='tax': d=3
                elif k=='wastewater': d=-2*f
                elif k=='road': d=-3
                elif k=='power': d=-(s.n('shop')+f)
                elif k=='parkdemand': d=-3 if s.n('green')<f else 0
                elif k=='forecast':
                    if not s.ds: s.refill()
                    top=s.ds[-1]; key='fire' if top[0]=='ffire' else top[0]
                    if key not in s.tot and s.pol!='casual': s.ds.insert(0,s.ds.pop())
                elif k=='drill': noroll=True
                elif k=='volunteers': m['vol']=m.get('vol',0)+1
                elif k=='material': m['mat']=m.get('mat',0)+2
                elif k=='totemsale': m['tdisc']=m.get('tdisc',0)+3
                elif k=='movein': m['free_house']=1
                elif k=='strike': m['nofac']=1
                elif k=='holiday': m['noshop']=1
                elif k=='tide': m['tide']=m.get('tide',0)+2
                s.coins=max(0,s.coins+d)
            s.coins+=s.income(m)
            if s.round>1 and not noroll and s.r.randint(1,6)+s.r.randint(1,6)<=s.risk(m):
                if not s.ds: s.refill()
                s.disaster(s.ds.pop())
            s.manage(m)
        return s.stars()
def run(cfg,pol,n=2000,seed=1):
    rng=random.Random(seed); S=[];H=[];C=[];D=[]
    for _ in range(n):
        g=G(cfg,pol,rng); S.append(g.play()); H.append(g.hits); C.append(g.coins); D.append(g.dis)
    return dict(stars=st.mean(S),best=sum(x==8 for x in S)/n*100,pass4=sum(x>=4 for x in S)/n*100,hits=st.mean(H),coins=st.mean(C),dis=st.mean(D))
BASE=dict(r0=2,esc=False,tp=(8,12,16,20),tot_from=3,hoard_at=7)
if __name__=='__main__':
    V={'v4 now':BASE,'A risk 4':dict(BASE,r0=4),'B totem 8/12/16/20':dict(BASE,esc=True),'A+B':dict(BASE,r0=4,esc=True)}
    for name,c in V.items():
        print('==',name)
        for pol in ('planner','planner_rand','hoarder','novice','casual'):
            o=run(c,pol); print(f"  {pol:13s} stars {o['stars']:.1f}  Best {o['best']:4.0f}%  >=4 {o['pass4']:4.0f}%  disasters {o['dis']:.1f}  hits {o['hits']:.1f}  coins left {o['coins']:.0f}")
