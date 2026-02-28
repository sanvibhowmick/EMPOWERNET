import os, math, pandas as pd
import psycopg2, psycopg2.extras
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DATABASE_URL","")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://","postgresql://",1)

def fetch(sql, params=None):
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=10)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ()); rows=[dict(r) for r in cur.fetchall()]
        conn.close(); return rows
    except Exception as e: print(f"[DB] {e}"); return []

def fetch_one(sql, params=None):
    r=fetch(sql,params); return r[0] if r else {}

C=dict(bg="#05080F",surface="#080D16",card="#0C1220",border="rgba(255,255,255,0.08)",
       cyan="#00E5FF",blue="#2979FF",emerald="#00E676",amber="#FFB300",rose="#FF4081",
       violet="#BB86FC",text="#E2EAF4",muted="#64748B",dim="#1E2D45")
FB="'DM Sans', sans-serif"; FM="'JetBrains Mono', monospace"; FH="'Syne', sans-serif"
GFONTS=("https://fonts.googleapis.com/css2?family=Syne:wght@700;800&"
        "family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap")
PALETTE=[C["cyan"],C["emerald"],C["amber"],C["rose"],C["violet"],C["blue"],
         "#FF6D00","#1DE9B6","#F06292","#80CBC4","#A5D6A7","#FFE082"]

WB_GEO={"type":"FeatureCollection","features":[
    {"type":"Feature","id":"KOLKATA","geometry":{"type":"Polygon","coordinates":[[[88.20,22.46],[88.47,22.46],[88.47,22.68],[88.20,22.68],[88.20,22.46]]]}},
    {"type":"Feature","id":"HOWRAH","geometry":{"type":"Polygon","coordinates":[[[87.95,22.35],[88.24,22.35],[88.24,22.80],[87.95,22.80],[87.95,22.35]]]}},
    {"type":"Feature","id":"HOOGHLY","geometry":{"type":"Polygon","coordinates":[[[87.55,22.50],[88.25,22.50],[88.25,23.15],[87.55,23.15],[87.55,22.50]]]}},
    {"type":"Feature","id":"NORTH 24 PARGANAS","geometry":{"type":"Polygon","coordinates":[[[88.25,22.60],[89.10,22.60],[89.10,23.40],[88.25,23.40],[88.25,22.60]]]}},
    {"type":"Feature","id":"SOUTH 24 PARGANAS","geometry":{"type":"Polygon","coordinates":[[[88.00,21.45],[89.20,21.45],[89.20,22.62],[88.00,22.62],[88.00,21.45]]]}},
    {"type":"Feature","id":"NADIA","geometry":{"type":"Polygon","coordinates":[[[88.10,22.95],[88.95,22.95],[88.95,23.90],[88.10,23.90],[88.10,22.95]]]}},
    {"type":"Feature","id":"MURSHIDABAD","geometry":{"type":"Polygon","coordinates":[[[87.75,23.85],[88.75,23.85],[88.75,24.72],[87.75,24.72],[87.75,23.85]]]}},
    {"type":"Feature","id":"BIRBHUM","geometry":{"type":"Polygon","coordinates":[[[87.20,23.55],[88.15,23.55],[88.15,24.35],[87.20,24.35],[87.20,23.55]]]}},
    {"type":"Feature","id":"PURBA BARDHAMAN","geometry":{"type":"Polygon","coordinates":[[[87.55,23.00],[88.30,23.00],[88.30,23.60],[87.55,23.60],[87.55,23.00]]]}},
    {"type":"Feature","id":"PASCHIM BARDHAMAN","geometry":{"type":"Polygon","coordinates":[[[86.90,23.20],[87.60,23.20],[87.60,23.80],[86.90,23.80],[86.90,23.20]]]}},
    {"type":"Feature","id":"BANKURA","geometry":{"type":"Polygon","coordinates":[[[86.60,22.70],[87.60,22.70],[87.60,23.35],[86.60,23.35],[86.60,22.70]]]}},
    {"type":"Feature","id":"PURULIA","geometry":{"type":"Polygon","coordinates":[[[85.85,22.70],[86.70,22.70],[86.70,23.45],[85.85,23.45],[85.85,22.70]]]}},
    {"type":"Feature","id":"JHARGRAM","geometry":{"type":"Polygon","coordinates":[[[86.20,22.00],[86.90,22.00],[86.90,22.75],[86.20,22.75],[86.20,22.00]]]}},
    {"type":"Feature","id":"PASCHIM MEDINIPUR","geometry":{"type":"Polygon","coordinates":[[[86.60,21.75],[87.45,21.75],[87.45,22.72],[86.60,22.72],[86.60,21.75]]]}},
    {"type":"Feature","id":"PURBA MEDINIPUR","geometry":{"type":"Polygon","coordinates":[[[87.40,21.60],[87.95,21.60],[87.95,22.55],[87.40,22.55],[87.40,21.60]]]}},
    {"type":"Feature","id":"MALDA","geometry":{"type":"Polygon","coordinates":[[[87.75,24.65],[88.40,24.65],[88.40,25.35],[87.75,25.35],[87.75,24.65]]]}},
    {"type":"Feature","id":"UTTAR DINAJPUR","geometry":{"type":"Polygon","coordinates":[[[87.75,25.30],[88.35,25.30],[88.35,26.20],[87.75,26.20],[87.75,25.30]]]}},
    {"type":"Feature","id":"DAKSHIN DINAJPUR","geometry":{"type":"Polygon","coordinates":[[[88.10,25.05],[88.75,25.05],[88.75,25.65],[88.10,25.65],[88.10,25.05]]]}},
    {"type":"Feature","id":"JALPAIGURI","geometry":{"type":"Polygon","coordinates":[[[88.40,26.25],[89.20,26.25],[89.20,26.90],[88.40,26.90],[88.40,26.25]]]}},
    {"type":"Feature","id":"DARJEELING","geometry":{"type":"Polygon","coordinates":[[[87.85,26.70],[88.55,26.70],[88.55,27.20],[87.85,27.20],[87.85,26.70]]]}},
    {"type":"Feature","id":"KALIMPONG","geometry":{"type":"Polygon","coordinates":[[[88.45,26.80],[88.85,26.80],[88.85,27.10],[88.45,27.10],[88.45,26.80]]]}},
    {"type":"Feature","id":"ALIPURDUAR","geometry":{"type":"Polygon","coordinates":[[[89.10,26.40],[89.75,26.40],[89.75,26.90],[89.10,26.90],[89.10,26.40]]]}},
    {"type":"Feature","id":"COOCH BEHAR","geometry":{"type":"Polygon","coordinates":[[[88.90,25.90],[89.60,25.90],[89.60,26.50],[88.90,26.50],[88.90,25.90]]]}},
]}
DC={"KOLKATA":(22.57,88.36),"HOWRAH":(22.59,88.10),"HOOGHLY":(22.90,87.90),
    "NORTH 24 PARGANAS":(22.99,88.68),"SOUTH 24 PARGANAS":(22.05,88.60),
    "NADIA":(23.47,88.52),"MURSHIDABAD":(24.18,88.27),"BIRBHUM":(23.90,87.70),
    "PURBA BARDHAMAN":(23.23,87.86),"PASCHIM BARDHAMAN":(23.50,87.25),
    "BANKURA":(23.23,87.07),"PURULIA":(23.33,86.36),"JHARGRAM":(22.45,86.53),
    "PASCHIM MEDINIPUR":(22.42,87.32),"PURBA MEDINIPUR":(22.08,87.68),
    "MALDA":(25.00,88.13),"UTTAR DINAJPUR":(25.75,88.05),"DAKSHIN DINAJPUR":(25.35,88.43),
    "JALPAIGURI":(26.55,88.72),"DARJEELING":(27.03,88.26),"KALIMPONG":(27.07,88.65),
    "ALIPURDUAR":(26.48,89.43),"COOCH BEHAR":(26.32,89.45)}
ALL_DISTRICTS=list(DC.keys())

# ── DATA ──────────────────────────────────────────────────────────────────────
def get_all_district_stats():
    s=fetch("SELECT UPPER(district) d,COUNT(*) n FROM self_help_groups GROUP BY UPPER(district)")
    u=fetch("SELECT UPPER(district) d,COUNT(*) n FROM user_profile GROUP BY UPPER(district)")
    t=fetch("SELECT UPPER(district) d,COUNT(*) n FROM training_programs GROUP BY UPPER(district)")
    sf=fetch("SELECT COALESCE(category,'Other') d,COUNT(*) n FROM safety_reports GROUP BY category")
    return ({r["d"]:int(r["n"]) for r in s},{r["d"]:int(r["n"]) for r in u},
            {r["d"]:int(r["n"]) for r in t},sum(int(r["n"]) for r in sf))

def get_state_kpis():
    return (int(fetch_one("SELECT COUNT(*) n FROM self_help_groups").get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM user_profile").get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM training_programs").get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM safety_reports").get("n",0)))

def get_district_kpis(d):
    clat,clon=DC.get(d,(23,87.8))
    return (int(fetch_one("SELECT COUNT(*) n FROM self_help_groups WHERE UPPER(district)=%s",(d,)).get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM user_profile WHERE UPPER(district)=%s",(d,)).get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM training_programs WHERE UPPER(district)=%s",(d,)).get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM safety_reports WHERE lat BETWEEN %s AND %s AND lon BETWEEN %s AND %s",(clat-.7,clat+.7,clon-.7,clon+.7)).get("n",0)))

def get_block_kpis(d,b):
    return (int(fetch_one("SELECT COUNT(*) n FROM self_help_groups WHERE UPPER(district)=%s AND UPPER(block)=%s",(d,b)).get("n",0)),
            int(fetch_one("SELECT COUNT(*) n FROM user_profile WHERE UPPER(district)=%s AND UPPER(block)=%s",(d,b)).get("n",0)),0,0)

def get_blocks_for_district(district):
    rows=fetch("""SELECT ah.block,COUNT(DISTINCT s.id) shg_count,COUNT(DISTINCT u.phone_number) user_count,
        AVG(ST_Y(ah.village_center_geog::geometry)) lat,AVG(ST_X(ah.village_center_geog::geometry)) lon
        FROM administrative_hierarchy ah
        LEFT JOIN self_help_groups s ON UPPER(s.district)=UPPER(ah.district) AND UPPER(s.block)=UPPER(ah.block)
        LEFT JOIN user_profile u ON UPPER(u.district)=UPPER(ah.district) AND UPPER(u.block)=UPPER(ah.block)
        WHERE UPPER(ah.district)=%s AND ah.village_center_geog IS NOT NULL GROUP BY ah.block""",(district,))
    if rows: return pd.DataFrame(rows)
    rows2=fetch("SELECT DISTINCT block,0 AS shg_count,0 AS user_count FROM self_help_groups WHERE UPPER(district)=%s LIMIT 30",(district,))
    if rows2:
        df=pd.DataFrame(rows2); df["lat"]=None; df["lon"]=None; return df
    return pd.DataFrame(columns=["block","shg_count","user_count","lat","lon"])

def get_villages_for_block(d,b):
    rows=fetch("""SELECT ah.village,ah.gram_panchayat,COUNT(DISTINCT s.id) shg_count,COUNT(DISTINCT u.phone_number) user_count,
        ST_Y(ah.village_center_geog::geometry) lat,ST_X(ah.village_center_geog::geometry) lon
        FROM administrative_hierarchy ah
        LEFT JOIN self_help_groups s ON UPPER(s.village)=UPPER(ah.village) AND UPPER(s.block)=UPPER(ah.block)
        LEFT JOIN user_profile u ON UPPER(u.village)=UPPER(ah.village) AND UPPER(u.block)=UPPER(ah.block)
        WHERE UPPER(ah.district)=%s AND UPPER(ah.block)=%s AND ah.village_center_geog IS NOT NULL
        GROUP BY ah.village,ah.gram_panchayat,ah.village_center_geog""",(d,b))
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["village","gram_panchayat","shg_count","user_count","lat","lon"])

def get_shgs_geo(d=None,b=None):
    if b: return fetch("SELECT shg_name,COALESCE(category,'—') cat,ST_Y(location_geog::geometry) lat,ST_X(location_geog::geometry) lon FROM self_help_groups WHERE location_geog IS NOT NULL AND UPPER(district)=%s AND UPPER(block)=%s LIMIT 400",(d,b))
    if d: return fetch("SELECT shg_name,COALESCE(category,'—') cat,ST_Y(location_geog::geometry) lat,ST_X(location_geog::geometry) lon FROM self_help_groups WHERE location_geog IS NOT NULL AND UPPER(district)=%s LIMIT 500",(d,))
    return fetch("SELECT shg_name,COALESCE(category,'—') cat,ST_Y(location_geog::geometry) lat,ST_X(location_geog::geometry) lon FROM self_help_groups WHERE location_geog IS NOT NULL LIMIT 800")

def get_safety_geo(d=None):
    if d:
        clat,clon=DC.get(d,(23,87.8))
        return fetch("SELECT COALESCE(category,'—') cat,description,lat,lon FROM safety_reports WHERE lat BETWEEN %s AND %s AND lon BETWEEN %s AND %s LIMIT 400",(clat-.7,clat+.7,clon-.7,clon+.7))
    return fetch("SELECT COALESCE(category,'—') cat,description,lat,lon FROM safety_reports LIMIT 600")

# ── chart data ────────────────────────────────────────────────────────────────

def get_vetted_jobs_by_category(d=None, b=None):
    """Count vetted jobs grouped by category. Falls back to state-level if district columns absent."""
    if b:
        rows = fetch("""SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt
                        FROM vetted_jobs WHERE UPPER(district)=%s AND UPPER(block)=%s
                        GROUP BY cat ORDER BY cnt DESC LIMIT 12""",(d,b))
        if rows: return rows
    if d:
        rows = fetch("""SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt
                        FROM vetted_jobs WHERE UPPER(district)=%s
                        GROUP BY cat ORDER BY cnt DESC LIMIT 12""",(d,))
        if rows: return rows
    return fetch("""SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt
                    FROM vetted_jobs GROUP BY cat ORDER BY cnt DESC LIMIT 12""")

def get_shg_category_dist(d=None, b=None):
    if b: return fetch("SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt FROM self_help_groups WHERE UPPER(district)=%s AND UPPER(block)=%s GROUP BY cat ORDER BY cnt DESC LIMIT 10",(d,b))
    if d: return fetch("SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt FROM self_help_groups WHERE UPPER(district)=%s GROUP BY cat ORDER BY cnt DESC LIMIT 10",(d,))
    return fetch("SELECT COALESCE(NULLIF(TRIM(category),''),'Other') cat,COUNT(*) cnt FROM self_help_groups GROUP BY cat ORDER BY cnt DESC LIMIT 10")

def get_safety_cats(d=None):
    if d:
        clat,clon=DC.get(d,(23,87.8))
        return fetch("SELECT COALESCE(category,'Other') cat,COUNT(*) cnt FROM safety_reports WHERE lat BETWEEN %s AND %s AND lon BETWEEN %s AND %s GROUP BY cat ORDER BY cnt DESC LIMIT 8",(clat-.7,clat+.7,clon-.7,clon+.7))
    return fetch("SELECT COALESCE(category,'Other') cat,COUNT(*) cnt FROM safety_reports GROUP BY cat ORDER BY cnt DESC LIMIT 8")

def get_occupation_dist(d=None, b=None):
    if b: return fetch("SELECT COALESCE(NULLIF(TRIM(primary_occupation),''),'Other') occ,COUNT(*) cnt FROM user_profile WHERE UPPER(district)=%s AND UPPER(block)=%s GROUP BY occ ORDER BY cnt DESC LIMIT 10",(d,b))
    if d: return fetch("SELECT COALESCE(NULLIF(TRIM(primary_occupation),''),'Other') occ,COUNT(*) cnt FROM user_profile WHERE UPPER(district)=%s GROUP BY occ ORDER BY cnt DESC LIMIT 10",(d,))
    return fetch("SELECT COALESCE(NULLIF(TRIM(primary_occupation),''),'Other') occ,COUNT(*) cnt FROM user_profile GROUP BY occ ORDER BY cnt DESC LIMIT 10")

# ── MAPS ──────────────────────────────────────────────────────────────────────
def mlay(lat,lon,zoom):
    return dict(mapbox=dict(style="carto-darkmatter",center=dict(lat=lat,lon=lon),zoom=zoom),
                margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(bgcolor="rgba(5,8,15,0.95)",bordercolor="rgba(0,229,255,0.2)",borderwidth=1,
                            font=dict(color="#64748B",size=10,family=FB),x=0.01,y=0.98,itemsizing="constant"),
                hoverlabel=dict(bgcolor="#050810",bordercolor=C["cyan"],font_color=C["text"],
                                font_family=FB,font_size=12))

def make_state_map(shg_d,usr_d,trn_d,sfe_total):
    z=[shg_d.get(d,0) for d in ALL_DISTRICTS]
    cd=[[shg_d.get(d,0),usr_d.get(d,0),trn_d.get(d,0)] for d in ALL_DISTRICTS]
    fig=go.Figure()
    fig.add_trace(go.Choroplethmapbox(
        geojson=WB_GEO,locations=ALL_DISTRICTS,z=z,featureidkey="id",
        colorscale=[[0,"#05111f"],[0.35,"#00395a"],[0.7,"#0099cc"],[1,"#00E5FF"]],
        marker_opacity=0.82,marker_line_width=1.5,marker_line_color="rgba(0,229,255,0.40)",
        colorbar=dict(title=dict(text="SHGs",font=dict(color=C["muted"],size=9,family=FB)),
                      thickness=8,len=0.55,x=0.99,tickfont=dict(color=C["muted"],size=8,family=FM),
                      bgcolor="rgba(0,0,0,0)",bordercolor="rgba(0,0,0,0)"),
        showscale=True,name="Districts",customdata=cd,
        hovertemplate=("<b style='font-size:13px'>%{location}</b><br>"
                       "──────────────<br>"
                       "👥 SHGs: <b>%{customdata[0]:,}</b><br>"
                       "👤 Users: <b>%{customdata[1]:,}</b><br>"
                       "🎓 Training: <b>%{customdata[2]:,}</b><extra></extra>")))
    rows=get_shgs_geo()
    if rows:
        df=pd.DataFrame(rows).dropna(subset=["lat","lon"])
        if not df.empty:
            fig.add_trace(go.Scattermapbox(lat=df["lat"],lon=df["lon"],mode="markers",
                marker=dict(size=5,color=C["emerald"],opacity=0.65),name="👥 SHGs",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                customdata=df[["shg_name","cat"]].values))
    rows2=get_safety_geo()
    if rows2:
        df2=pd.DataFrame(rows2).dropna(subset=["lat","lon"])
        if not df2.empty:
            fig.add_trace(go.Scattermapbox(lat=df2["lat"],lon=df2["lon"],mode="markers",
                marker=dict(size=6,color=C["rose"],opacity=0.70),name="⚠️ Safety",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                customdata=df2[["cat","description"]].fillna("").values))
    fig.update_layout(**mlay(23.5,87.85,5.6))
    return fig

def make_district_map(district,blocks_df):
    clat,clon=DC.get(district,(23,87.8))
    fig=go.Figure()
    feat=next((f for f in WB_GEO["features"] if f["id"]==district),None)
    if feat:
        coords=feat["geometry"]["coordinates"][0]
        fig.add_trace(go.Scattermapbox(lat=[c[1] for c in coords]+[coords[0][1]],
            lon=[c[0] for c in coords]+[coords[0][0]],mode="lines",
            line=dict(color=C["cyan"],width=2.5),hoverinfo="none",showlegend=False))
    if not blocks_df.empty:
        df=blocks_df.copy()
        df["shg_count"]=pd.to_numeric(df["shg_count"],errors="coerce").fillna(0)
        df["user_count"]=pd.to_numeric(df["user_count"],errors="coerce").fillna(0)
        df["lat"]=pd.to_numeric(df.get("lat",pd.Series([None]*len(df))),errors="coerce")
        df["lon"]=pd.to_numeric(df.get("lon",pd.Series([None]*len(df))),errors="coerce")
        valid=df.dropna(subset=["lat","lon"])
        if valid.empty:
            n=len(df); df=df.copy()
            df["lat"]=[clat+0.20*math.sin(2*math.pi*i/max(n,1)) for i in range(n)]
            df["lon"]=[clon+0.25*math.cos(2*math.pi*i/max(n,1)) for i in range(n)]
            valid=df
        mx=max(float(valid["shg_count"].max()),1)
        sizes=(valid["shg_count"]/mx*26+12).tolist()
        cd=[["BLOCK",str(row["block"]),int(row["shg_count"]),int(row["user_count"])] for _,row in valid.iterrows()]
        fig.add_trace(go.Scattermapbox(lat=valid["lat"].tolist(),lon=valid["lon"].tolist(),
            mode="markers+text",marker=dict(size=sizes,color=C["cyan"],opacity=0.88),
            text=valid["block"].str.upper().str[:10],
            textfont=dict(color="#E2EAF4",size=9,family=FB),textposition="top center",
            name="🔷 Blocks",customdata=cd,
            hovertemplate=("<b>%{customdata[1]}</b><br>"
                           "👥 SHGs: <b>%{customdata[2]}</b><br>"
                           "👤 Users: <b>%{customdata[3]}</b><extra></extra>")))
    rows=get_shgs_geo(d=district)
    if rows:
        df2=pd.DataFrame(rows).dropna(subset=["lat","lon"])
        if not df2.empty:
            fig.add_trace(go.Scattermapbox(lat=df2["lat"],lon=df2["lon"],mode="markers",
                marker=dict(size=6,color=C["emerald"],opacity=0.75),name="👥 SHGs",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                customdata=df2[["shg_name","cat"]].fillna("—").values))
    rows3=get_safety_geo(d=district)
    if rows3:
        df3=pd.DataFrame(rows3).dropna(subset=["lat","lon"])
        if not df3.empty:
            fig.add_trace(go.Scattermapbox(lat=df3["lat"],lon=df3["lon"],mode="markers",
                marker=dict(size=7,color=C["rose"],opacity=0.80),name="⚠️ Safety",
                hovertemplate="<b>%{customdata[0]}</b><extra></extra>",
                customdata=df3[["cat"]].fillna("—").values))
    fig.update_layout(**mlay(clat,clon,8.2))
    return fig

def make_block_map(district,block,vdf):
    clat,clon=DC.get(district,(23,87.8))
    fig=go.Figure()
    if not vdf.empty:
        df=vdf.copy()
        df["lat"]=pd.to_numeric(df["lat"],errors="coerce")
        df["lon"]=pd.to_numeric(df["lon"],errors="coerce")
        valid=df.dropna(subset=["lat","lon"])
        if not valid.empty:
            clat=float(valid["lat"].mean()); clon=float(valid["lon"].mean())
            mx=max(float(pd.to_numeric(valid["user_count"],errors="coerce").fillna(0).max()),1)
            sizes=(pd.to_numeric(valid["user_count"],errors="coerce").fillna(0)/mx*18+8).tolist()
            fig.add_trace(go.Scattermapbox(lat=valid["lat"].tolist(),lon=valid["lon"].tolist(),
                mode="markers+text",marker=dict(size=sizes,color=C["violet"],opacity=0.88),
                text=valid["village"].str[:12],textfont=dict(color="#E2EAF4",size=8,family=FB),
                textposition="top center",name="🏘️ Villages",
                hovertemplate=("<b>%{customdata[0]}</b><br>GP: %{customdata[1]}<br>"
                               "👥 SHGs: <b>%{customdata[2]}</b><br>👤 Users: <b>%{customdata[3]}</b><extra></extra>"),
                customdata=valid[["village","gram_panchayat","shg_count","user_count"]].fillna("—").values))
    rows=get_shgs_geo(d=district,b=block)
    if rows:
        df2=pd.DataFrame(rows).dropna(subset=["lat","lon"])
        if not df2.empty:
            fig.add_trace(go.Scattermapbox(lat=df2["lat"],lon=df2["lon"],mode="markers",
                marker=dict(size=9,color=C["emerald"],opacity=0.88),name="👥 SHGs",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                customdata=df2[["shg_name","cat"]].fillna("—").values))
    fig.update_layout(**mlay(clat,clon,11.0))
    return fig

# ── CHART BASE ────────────────────────────────────────────────────────────────
def cbase(title, h, accent=None):
    ac = accent or C["cyan"]
    return dict(
        title=dict(text=f"<b>{title}</b>",
                   font=dict(color="#94A3B8", size=10, family=FB), x=0.01, y=0.97),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=h,
        hoverlabel=dict(
            bgcolor="#080D16", font_color=C["text"], font_family=FB, font_size=12,
            bordercolor=ac,
        ),
        font=dict(family=FB, color=C["muted"]),
        margin=dict(l=10, r=10, t=36, b=10),
    )

# ── CHART 1 ── TREEMAP: Vetted Jobs by Category ───────────────────────────────
def make_treemap_chart(d=None, b=None):
    rows = get_vetted_jobs_by_category(d, b)
    if not rows:
        rows = [{"cat": "No data", "cnt": 1}]
    df = pd.DataFrame(rows)
    df["cnt"] = pd.to_numeric(df["cnt"], errors="coerce").fillna(0).astype(int)
    total = df["cnt"].sum() or 1
    df["pct"] = (df["cnt"] / total * 100).round(1)
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(df))]

    fig = go.Figure(go.Treemap(
        labels=df["cat"].tolist(),
        parents=[""] * len(df),
        values=df["cnt"].tolist(),
        customdata=df["pct"].tolist(),
        texttemplate="<b>%{label}</b><br><span style='font-size:13px'>%{value:,}</span><br><span style='opacity:0.7'>%{customdata}%</span>",
        textfont=dict(family=FB, size=11, color="#FFFFFF"),
        hovertemplate="<b>%{label}</b><br>Jobs: <b>%{value:,}</b><br>Share: <b>%{customdata}%</b><extra></extra>",
        marker=dict(
            colors=colors,
            line=dict(width=2.5, color=C["bg"]),
            pad=dict(t=8, l=5, r=5, b=5),
            cornerradius=4,
        ),
        pathbar_visible=False,
    ))
    layout = cbase("VETTED JOBS BY CATEGORY", 290, C["amber"])
    layout.update(margin=dict(l=4, r=4, t=36, b=4))
    fig.update_layout(**layout)
    return fig

# ── CHART 2 ── POLAR ROSE (Barpolar): SHG Category Distribution ──────────────
def make_polar_chart(d=None, b=None):
    rows = get_shg_category_dist(d, b)
    if not rows:
        rows = [{"cat": "No data", "cnt": 1}]
    df = pd.DataFrame(rows)
    df["cnt"] = pd.to_numeric(df["cnt"], errors="coerce").fillna(0).astype(int)
    n = len(df)
    theta = [round(i * 360 / n, 1) for i in range(n)]
    colors = [PALETTE[i % len(PALETTE)] for i in range(n)]

    fig = go.Figure()
    for i, row in df.iterrows():
        fig.add_trace(go.Barpolar(
            r=[int(row["cnt"])],
            theta=[theta[i]],
            width=[max(360 / n - 3, 12)],
            name=str(row["cat"]),
            marker_color=colors[i],
            marker_line_color=C["bg"],
            marker_line_width=2,
            opacity=0.92,
            hovertemplate=f"<b>{row['cat']}</b><br>SHGs: <b>{int(row['cnt']):,}</b><extra></extra>",
        ))

    layout = cbase("SHG CATEGORIES — POLAR", 290, C["violet"])
    layout.update(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(
                tickfont=dict(color="#94A3B8", size=8, family=FB),
                linecolor="rgba(255,255,255,0.08)", gridcolor="rgba(255,255,255,0.06)",
                tickvals=theta,
                ticktext=df["cat"].str[:13].tolist(),
                direction="clockwise", rotation=90,
            ),
            radialaxis=dict(
                visible=True,
                tickfont=dict(color=C["dim"], size=7, family=FM),
                gridcolor="rgba(187,134,252,0.12)",
                linecolor="rgba(0,0,0,0)",
                showticklabels=False,
            ),
        ),
        showlegend=False,
        margin=dict(l=55, r=55, t=46, b=46),
    )
    fig.update_layout(**layout)
    return fig

# ── CHART 3 ── FUNNEL: Safety Reports by Category ────────────────────────────
def make_funnel_chart(d=None):
    rows = get_safety_cats(d)
    if not rows:
        rows = [{"cat": "No data", "cnt": 1}]
    df = pd.DataFrame(rows)
    df["cnt"] = pd.to_numeric(df["cnt"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values("cnt", ascending=False)

    rose_scale = ["#FF4081","#E91E63","#C2185B","#9C1045","#6d0830","#42061e","#250513","#110209"]
    bar_colors = [rose_scale[min(i, len(rose_scale)-1)] for i in range(len(df))]

    fig = go.Figure(go.Funnel(
        y=df["cat"].tolist(),
        x=df["cnt"].tolist(),
        textposition="inside",
        textinfo="value+percent initial",
        textfont=dict(family=FM, size=10, color="#FFFFFF"),
        hovertemplate="<b>%{y}</b><br>Reports: <b>%{x:,}</b><br>%{percentInitial} of total<extra></extra>",
        marker=dict(color=bar_colors, line=dict(width=2, color=C["bg"])),
        connector=dict(line=dict(color="rgba(255,64,129,0.25)", width=1.5, dash="dot")),
        opacity=0.95,
    ))
    layout = cbase("SAFETY INCIDENTS — FUNNEL", 290, C["rose"])
    layout.update(
        margin=dict(l=10, r=10, t=36, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(color="#94A3B8", size=10, family=FB)),
    )
    fig.update_layout(**layout)
    return fig

# ── CHART 4 ── LOLLIPOP: User Occupations ────────────────────────────────────
def make_lollipop_chart(d=None, b=None):
    rows = get_occupation_dist(d, b)
    if not rows:
        rows = [{"occ": "No data", "cnt": 1}]
    df = pd.DataFrame(rows)
    df["cnt"] = pd.to_numeric(df["cnt"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values("cnt", ascending=True)

    fig = go.Figure()
    # Stem lines
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[0, int(row["cnt"])],
            y=[row["occ"], row["occ"]],
            mode="lines",
            line=dict(color="rgba(0,229,255,0.22)", width=2),
            showlegend=False, hoverinfo="skip",
        ))
    # Dots + labels
    fig.add_trace(go.Scatter(
        x=df["cnt"].tolist(),
        y=df["occ"].tolist(),
        mode="markers+text",
        marker=dict(
            size=16,
            color=df["cnt"].tolist(),
            colorscale=[[0,"#002a42"],[0.35,"#005580"],[0.7,"#0099cc"],[1,"#00E5FF"]],
            showscale=False,
            line=dict(width=2.5, color=C["bg"]),
        ),
        text=df["cnt"].apply(lambda v: f"{v:,}"),
        textposition="middle right",
        textfont=dict(color="#94A3B8", size=9, family=FM),
        hovertemplate="<b>%{y}</b><br>Users: <b>%{x:,}</b><extra></extra>",
        showlegend=False,
        cliponaxis=False,
    ))

    layout = cbase("USER OCCUPATIONS — TOP 10", 290, C["cyan"])
    mx = int(df["cnt"].max()) if len(df) else 1
    layout.update(
        margin=dict(l=10, r=74, t=36, b=10),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-mx*0.03, mx*1.30]),
        yaxis=dict(tickfont=dict(color="#94A3B8", size=10, family=FB),
                   gridcolor="rgba(0,0,0,0)", automargin=True),
    )
    fig.update_layout(**layout)
    return fig

# ── TABLE ─────────────────────────────────────────────────────────────────────
CELL=dict(backgroundColor=C["card"],color=C["text"],fontFamily=FM,fontSize="11px",
          border=f"1px solid {C['border']}",padding="8px 14px",whiteSpace="normal")
HEADR=dict(backgroundColor="#080C12",color=C["cyan"],fontFamily=FB,fontWeight="600",
           fontSize="10px",letterSpacing="1px",textTransform="uppercase",
           border=f"1px solid {C['border']}",padding="10px 14px")

def make_table(tab,state):
    d=state.get("district"); b=state.get("block")
    if tab=="tab-shgs":
        if b: rows=fetch("SELECT shg_name \"SHG\",leader_name \"Leader\",category \"Cat\",contact_number \"Contact\",formation_date::text \"Formed\" FROM self_help_groups WHERE UPPER(district)=%s AND UPPER(block)=%s LIMIT 100",(d,b))
        elif d: rows=fetch("SELECT shg_name \"SHG\",leader_name \"Leader\",block \"Block\",category \"Cat\",formation_date::text \"Formed\" FROM self_help_groups WHERE UPPER(district)=%s LIMIT 100",(d,))
        else: rows=fetch("SELECT shg_name \"SHG\",district \"District\",block \"Block\",category \"Cat\",formation_date::text \"Formed\" FROM self_help_groups ORDER BY id DESC LIMIT 100")
        df=pd.DataFrame(rows) if rows else pd.DataFrame(columns=["SHG","District","Block","Cat","Formed"])
    elif tab=="tab-training":
        if d: rows=fetch("SELECT course_name \"Course\",agency_name \"Agency\",skill_level \"Level\",duration_hours \"Hrs\",course_fee::text \"Fee(₹)\" FROM training_programs WHERE UPPER(district)=%s LIMIT 100",(d,))
        else: rows=fetch("SELECT course_name \"Course\",agency_name \"Agency\",district \"District\",skill_level \"Level\",duration_hours \"Hrs\" FROM training_programs ORDER BY id DESC LIMIT 100")
        df=pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Course","Agency","District","Level","Hrs"])
    elif tab=="tab-users":
        if b: rows=fetch("SELECT full_name \"Name\",village \"Village\",primary_occupation \"Occupation\",skill_level \"Skill\" FROM user_profile WHERE UPPER(district)=%s AND UPPER(block)=%s LIMIT 100",(d,b))
        elif d: rows=fetch("SELECT full_name \"Name\",block \"Block\",primary_occupation \"Occupation\",skill_level \"Skill\" FROM user_profile WHERE UPPER(district)=%s LIMIT 100",(d,))
        else: rows=fetch("SELECT full_name \"Name\",district \"District\",block \"Block\",primary_occupation \"Occupation\",skill_level \"Skill\" FROM user_profile ORDER BY created_at DESC LIMIT 100")
        df=pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Name","District","Block","Occupation","Skill"])
    else:
        if d:
            clat,clon=DC.get(d,(23,87.8))
            rows=fetch("SELECT description \"Description\",category \"Category\",TO_CHAR(reported_at,'DD Mon YYYY') \"Reported\" FROM safety_reports WHERE lat BETWEEN %s AND %s AND lon BETWEEN %s AND %s ORDER BY reported_at DESC LIMIT 100",(clat-.7,clat+.7,clon-.7,clon+.7))
        else: rows=fetch("SELECT description \"Description\",category \"Category\",TO_CHAR(reported_at,'DD Mon YYYY') \"Reported\" FROM safety_reports ORDER BY reported_at DESC LIMIT 100")
        df=pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Description","Category","Reported"])
    return dash_table.DataTable(data=df.to_dict("records"),columns=[{"name":c,"id":c} for c in df.columns],
        style_cell=CELL,style_header=HEADR,
        style_data_conditional=[{"if":{"row_index":"odd"},"backgroundColor":"#0a1220"}],
        page_size=8,style_table={"borderRadius":"8px","overflow":"hidden","overflowX":"auto"})

# ── LAYOUT ────────────────────────────────────────────────────────────────────
CARD={
    "background":"linear-gradient(145deg,#0D1525,#080D16)",
    "borderRadius":"14px",
    "border":"1px solid rgba(255,255,255,0.07)",
    "padding":"16px 18px",
    "boxShadow":"0 4px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)",
}

def card_with_accent(accent):
    """Card with a glowing top-edge accent line."""
    return {
        **CARD,
        "borderTop": f"1px solid {accent}60",
        "boxShadow": f"0 4px 28px rgba(0,0,0,0.55), 0 0 0 0 transparent, inset 0 1px 0 {accent}30",
    }

def kpi_card(kid,label,value,accent,icon):
    return html.Div([
        html.Div(icon,style={
            "fontSize":"22px","width":"46px","height":"46px","borderRadius":"12px",
            "display":"flex","alignItems":"center","justifyContent":"center","flexShrink":"0",
            "background":f"linear-gradient(135deg,{accent}30,{accent}08)",
            "border":f"1px solid {accent}50","marginRight":"16px",
            "boxShadow":f"0 0 18px {accent}20",
        }),
        html.Div([
            html.Div(label,style={
                "color":C["muted"],"fontSize":"9px","textTransform":"uppercase",
                "letterSpacing":"1.8px","fontFamily":FB,"fontWeight":"600","marginBottom":"5px",
            }),
            html.Div(value,id=kid,style={
                "color":C["text"],"fontSize":"24px","fontWeight":"700","fontFamily":FM,
                "lineHeight":"1","textShadow":f"0 0 20px {accent}55",
            }),
        ])
    ],style={
        "display":"flex","alignItems":"center",
        "background":f"linear-gradient(135deg,{accent}0D 0%,#0C1220 60%)",
        "padding":"20px 22px","borderRadius":"14px",
        "border":f"1px solid {accent}28",
        "borderTop":f"1px solid {accent}55",
        "boxShadow":f"0 4px 28px rgba(0,0,0,0.5), 0 0 40px {accent}08",
        "flex":"1","position":"relative","overflow":"hidden",
    })

app=dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP,GFONTS],
              suppress_callback_exceptions=True,title="EmpowerNet · WB")

app.layout=html.Div([
    dcc.Store(id="drill-state",data={"level":"state","district":None,"block":None}),
    dcc.Store(id="blocks-store",data=[]),

    # ── Header ──
    html.Div([html.Div([
        html.Div([
            html.Span("empower",style={"fontFamily":FH,"fontSize":"22px","fontWeight":"800","color":C["cyan"]}),
            html.Span("net",style={"fontFamily":FH,"fontSize":"22px","fontWeight":"800","color":C["text"]}),
            html.Span("WEST BENGAL",style={"fontFamily":FM,"fontSize":"9px","color":C["muted"],"marginLeft":"10px",
                "letterSpacing":"2px","border":f"1px solid {C['dim']}","padding":"2px 6px","borderRadius":"3px"}),
        ],style={"display":"flex","alignItems":"baseline","gap":"1px"}),
        html.Div([
            html.Span("WB",style={"fontFamily":FM,"fontSize":"10px","color":C["cyan"]}),
            html.Span(id="bc-dist",style={"fontFamily":FM,"fontSize":"10px","color":C["muted"]}),
            html.Span(id="bc-block",style={"fontFamily":FM,"fontSize":"10px","color":C["muted"]}),
        ],style={"display":"flex","alignItems":"center","gap":"3px"}),
        html.Div([
            html.Span(id="level-badge"),
            html.Button("⟲ RESET",id="reset-btn",style={"background":"transparent",
                "border":f"1px solid {C['cyan']}50","color":C["cyan"],"fontFamily":FM,
                "fontSize":"9px","letterSpacing":"1px","padding":"5px 14px","borderRadius":"6px","cursor":"pointer"}),
        ],style={"display":"flex","alignItems":"center","gap":"10px"}),
    ],style={"display":"flex","alignItems":"center","justifyContent":"space-between","maxWidth":"1700px","margin":"0 auto"})],
    style={"background":"linear-gradient(180deg,#080D16 0%,#05080F 100%)",
           "borderBottom":f"1px solid rgba(0,229,255,0.15)",
           "boxShadow":"0 2px 30px rgba(0,0,0,0.6), 0 1px 0 rgba(0,229,255,0.08)",
           "padding":"12px 28px","position":"sticky","top":"0","zIndex":"100"}),

    # ── Body ──
    html.Div([
        html.Div([
            kpi_card("kpi-shg","Active SHGs","—",C["emerald"],"👥"),
            kpi_card("kpi-users","Registered Users","—",C["cyan"],"👤"),
            kpi_card("kpi-train","Training Programs","—",C["amber"],"🎓"),
            kpi_card("kpi-safety","Safety Reports","—",C["rose"],"⚠️"),
        ],style={"display":"flex","gap":"14px","marginBottom":"18px"}),

        html.Div([
            # Left — map
            html.Div([html.Div([
                html.Div([
                    html.Span("GEOGRAPHY",style={"fontFamily":FB,"fontSize":"9px","color":C["muted"],"letterSpacing":"2px","fontWeight":"600"}),
                    html.Span(id="map-hint",style={"fontFamily":FM,"fontSize":"9px","color":C["blue"]}),
                ],style={"display":"flex","justifyContent":"space-between","marginBottom":"6px"}),
                html.Div([
                    html.Span("● SHGs",style={"color":C["emerald"],"fontSize":"9px","marginRight":"14px","fontFamily":FB}),
                    html.Span("▲ Safety",style={"color":C["rose"],"fontSize":"9px","marginRight":"14px","fontFamily":FB}),
                    html.Span("● Blocks",style={"color":C["cyan"],"fontSize":"9px","marginRight":"14px","fontFamily":FB}),
                    html.Span("● Villages",style={"color":C["violet"],"fontSize":"9px","fontFamily":FB}),
                ],style={"marginBottom":"8px"}),
                dcc.Graph(id="map-visual",config={"displayModeBar":False,"scrollZoom":True},
                          style={"height":"570px","borderRadius":"8px","overflow":"hidden"}),
            ],style=card_with_accent(C["cyan"]))],style={"flex":"0 0 44%","minWidth":"0"}),

            # Right — 2×2 charts + table
            html.Div([
                # Row 1
                html.Div([
                    html.Div([dcc.Graph(id="treemap-chart",config={"displayModeBar":False},style={"height":"290px"})],
                             style={**card_with_accent(C["amber"]),"flex":"0 0 57%"}),
                    html.Div([dcc.Graph(id="polar-chart",config={"displayModeBar":False},style={"height":"290px"})],
                             style={**card_with_accent(C["violet"]),"flex":"1"}),
                ],style={"display":"flex","gap":"14px","marginBottom":"14px"}),
                # Row 2
                html.Div([
                    html.Div([dcc.Graph(id="funnel-chart",config={"displayModeBar":False},style={"height":"290px"})],
                             style={**card_with_accent(C["rose"]),"flex":"1"}),
                    html.Div([dcc.Graph(id="lollipop-chart",config={"displayModeBar":False},style={"height":"290px"})],
                             style={**card_with_accent(C["cyan"]),"flex":"1"}),
                ],style={"display":"flex","gap":"14px","marginBottom":"14px"}),
                # Table
                html.Div([
                    html.Div([
                        html.Button("👥 SHGs",id="tab-shgs-btn",n_clicks=0,className="tab-btn tab-active"),
                        html.Button("🎓 Training",id="tab-train-btn",n_clicks=0,className="tab-btn"),
                        html.Button("👤 Users",id="tab-users-btn",n_clicks=0,className="tab-btn"),
                        html.Button("⚠️ Safety",id="tab-safety-btn",n_clicks=0,className="tab-btn"),
                    ],style={"display":"flex","gap":"6px","marginBottom":"14px"}),
                    dcc.Store(id="active-tab",data="tab-shgs"),
                    html.Div(id="table-container"),
                ],style=card_with_accent(C["blue"])),
            ],style={"flex":"1","minWidth":"0","display":"flex","flexDirection":"column"}),
        ],style={"display":"flex","gap":"16px","alignItems":"flex-start"}),
    ],style={"maxWidth":"1700px","margin":"0 auto","padding":"22px 28px"}),
],style={"backgroundColor":C["bg"],"minHeight":"100vh","fontFamily":FB})

app.index_string='''<!DOCTYPE html>
<html><head>{%metas%}<title>EmpowerNet · West Bengal</title>{%favicon%}{%css%}
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
  background:#05080F;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% -10%,rgba(0,229,255,0.04) 0%,transparent 60%),
    radial-gradient(ellipse 60% 40% at 85% 100%,rgba(41,121,255,0.05) 0%,transparent 55%);
  overflow-x:hidden;
  min-height:100vh;
}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#05080F}
::-webkit-scrollbar-thumb{background:#1a2840;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#253a55}

/* Tab buttons */
.tab-btn{
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.08);
  color:#4B5E78;
  font-family:'DM Sans',sans-serif;font-size:9px;font-weight:600;
  letter-spacing:1.5px;text-transform:uppercase;
  padding:7px 18px;border-radius:8px;cursor:pointer;
  transition:all .2s ease;
  position:relative;overflow:hidden;
}
.tab-btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,0.04),transparent);
  opacity:0;transition:opacity .2s;
}
.tab-btn:hover{
  border-color:rgba(0,229,255,0.3);
  color:#94A3B8;
  background:rgba(0,229,255,0.05);
}
.tab-btn:hover::before{opacity:1}
.tab-active{
  border-color:rgba(0,229,255,0.55)!important;
  color:#00E5FF!important;
  background:linear-gradient(135deg,rgba(0,229,255,0.12),rgba(0,229,255,0.04))!important;
  box-shadow:0 0 18px rgba(0,229,255,0.15), inset 0 1px 0 rgba(0,229,255,0.2)!important;
}

/* KPI card glow pulse on hover */
.kpi-hover:hover{
  box-shadow:0 6px 40px rgba(0,0,0,0.6)!important;
  transform:translateY(-1px);
  transition:all .25s ease;
}

/* Chart container inner breathing shadow */
.dash-graph{
  border-radius:8px;
  overflow:hidden;
}

/* Plotly modebar hide */
.modebar{display:none!important}
</style>
</head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''

# ── CALLBACKS ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("drill-state","data"), Output("blocks-store","data"),
    Input("map-visual","clickData"), Input("reset-btn","n_clicks"),
    State("drill-state","data"), prevent_initial_call=False)
def handle_drill(clickData,reset_n,state):
    ctx=callback_context
    if not ctx.triggered or ctx.triggered[0]["prop_id"]==".":
        return {"level":"state","district":None,"block":None},[]
    tid=ctx.triggered[0]["prop_id"].split(".")[0]
    if tid=="reset-btn":
        return {"level":"state","district":None,"block":None},[]
    if tid=="map-visual" and clickData:
        pt=clickData["points"][0]
        curve=pt.get("curveNumber",-1)
        if state["level"]=="state":
            if curve==0:  # choropleth only — scatter overlays must NOT trigger drill
                district=pt.get("location","").strip()
                if district and district in ALL_DISTRICTS:
                    bdf=get_blocks_for_district(district)
                    return {"level":"district","district":district,"block":None},bdf.to_dict("records")
        elif state["level"]=="district":
            cd=pt.get("customdata",None)
            if cd and len(cd)>=2 and str(cd[0])=="BLOCK":
                blk=str(cd[1]).strip()
                if blk:
                    return {"level":"block","district":state["district"],"block":blk},[]
    return state,[]

@app.callback(
    Output("active-tab","data"),
    Output("tab-shgs-btn","className"),Output("tab-train-btn","className"),
    Output("tab-users-btn","className"),Output("tab-safety-btn","className"),
    Input("tab-shgs-btn","n_clicks"),Input("tab-train-btn","n_clicks"),
    Input("tab-users-btn","n_clicks"),Input("tab-safety-btn","n_clicks"),
    prevent_initial_call=False)
def switch_tab(a,b,c,d):
    ctx=callback_context; ON,OFF="tab-btn tab-active","tab-btn"
    if not ctx.triggered or ctx.triggered[0]["prop_id"]==".": return "tab-shgs",ON,OFF,OFF,OFF
    tid=ctx.triggered[0]["prop_id"].split(".")[0]
    m={"tab-shgs-btn":("tab-shgs",ON,OFF,OFF,OFF),"tab-train-btn":("tab-training",OFF,ON,OFF,OFF),
       "tab-users-btn":("tab-users",OFF,OFF,ON,OFF),"tab-safety-btn":("tab-safety",OFF,OFF,OFF,ON)}
    return m.get(tid,("tab-shgs",ON,OFF,OFF,OFF))

@app.callback(
    Output("map-visual","figure"),
    Output("treemap-chart","figure"),
    Output("polar-chart","figure"),
    Output("funnel-chart","figure"),
    Output("lollipop-chart","figure"),
    Output("kpi-shg","children"),Output("kpi-users","children"),
    Output("kpi-train","children"),Output("kpi-safety","children"),
    Output("bc-dist","children"),Output("bc-block","children"),
    Output("level-badge","children"),Output("map-hint","children"),
    Output("table-container","children"),
    Input("drill-state","data"),Input("blocks-store","data"),Input("active-tab","data"))
def update_all(state,blocks_data,tab):
    lvl=state["level"]; dis=state.get("district"); blk=state.get("block")

    if lvl=="state":      s,u,t,sf=get_state_kpis()
    elif lvl=="district": s,u,t,sf=get_district_kpis(dis)
    else:                 s,u,t,sf=get_block_kpis(dis,blk)

    if lvl=="state":
        shg_d,usr_d,trn_d,_=get_all_district_stats()
        mfig=make_state_map(shg_d,usr_d,trn_d,sf)
    elif lvl=="district":
        bdf=pd.DataFrame(blocks_data) if blocks_data else get_blocks_for_district(dis)
        mfig=make_district_map(dis,bdf)
    else:
        vdf=get_villages_for_block(dis,blk)
        mfig=make_block_map(dis,blk,vdf)

    bmap={"state":(C["cyan"],"STATE VIEW"),"district":(C["amber"],"DISTRICT"),"block":(C["emerald"],"BLOCK")}
    bc,bl=bmap[lvl]
    badge=html.Span(bl,style={"fontFamily":FM,"fontSize":"8px","letterSpacing":"1.5px","color":bc,
        "border":f"1px solid {bc}50","backgroundColor":f"{bc}10","padding":"3px 10px","borderRadius":"4px"})
    hints={"state":"Hover for stats · Click district choropleth to drill in",
           "district":"Click a block bubble to drill in","block":"Village-level view"}

    return (
        mfig,
        make_treemap_chart(dis, blk),
        make_polar_chart(dis, blk),
        make_funnel_chart(dis),
        make_lollipop_chart(dis, blk),
        f"{s:,}", f"{u:,}", f"{t:,}", f"{sf:,}",
        f" › {dis}" if dis else "",
        "" if not blk else f" › {blk}",
        badge, hints[lvl],
        make_table(tab, state),
    )

if __name__=="__main__":
    app.run(debug=True,port=8050,host="0.0.0.0")