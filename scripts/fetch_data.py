"""
정부 지원금 자동 수집 스크립트
매일 GitHub Actions에서 자동 실행되어 최신 지원사업 정보를 수집하고
대시보드 HTML을 자동 업데이트합니다.

사용하는 API:
1. 기업마당(bizinfo.go.kr) - 중소벤처기업부 지원사업 공고
2. 공공데이터포털 보조금24 API - 정부 보조금/복지 서비스
"""

import requests
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BIZINFO_API_KEY = os.environ.get("BIZINFO_API_KEY", "")
DATA_GO_KR_API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "")
YOUTH_API_KEY = os.environ.get("YOUTH_API_KEY", "")  # 온통청년 API

TODAY = datetime.now().strftime("%Y%m%d")
THIRTY_DAYS_AGO = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

OUTPUT_DIR = Path(__file__).parent.parent
DATA_FILE = OUTPUT_DIR / "data.json"
HTML_FILE = OUTPUT_DIR / "index.html"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 카테고리 자동 분류
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATEGORY_KEYWORDS = {
    "small_biz": ["소상공인", "소공인", "전통시장", "상점가", "상권", "영세", "자영업", "폐업", "재기"],
    "startup": ["창업", "예비창업", "스타트업", "벤처", "사관학교", "액셀러레이터", "창진원"],
    "employment": ["고용", "취업", "일자리", "채용", "인턴", "근로", "청년일자리", "장려금", "구직"],
    "tech": ["기술", "R&D", "연구개발", "스마트공장", "혁신", "특허", "디지털전환", "AI활용"],
    "agriculture": ["농업", "농림", "수산", "축산", "귀농", "귀촌", "영농"],
    "welfare": ["복지", "생계", "긴급", "의료", "주거", "돌봄", "양육", "출산", "보육", "월세"],
    "education": ["교육", "훈련", "배움", "디지털트레이닝", "KDT", "직업훈련", "인재양성"],
}

def classify_category(title, description=""):
    """제목과 설명으로 카테고리 자동 분류"""
    text = f"{title} {description}".lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return "small_biz"  # 기본값


def detect_region(title, org):
    """기관명/제목에서 지역 추출"""
    regions = {
        "서울": ["서울"],
        "부산": ["부산"],
        "대구": ["대구"],
        "인천": ["인천"],
        "광주": ["광주"],
        "대전": ["대전"],
        "울산": ["울산"],
        "세종": ["세종"],
        "경기": ["경기"],
        "강원": ["강원"],
        "충북": ["충북", "충청북"],
        "충남": ["충남", "충청남"],
        "전북": ["전북", "전라북"],
        "전남": ["전남", "전라남"],
        "경북": ["경북", "경상북"],
        "경남": ["경남", "경상남"],
        "제주": ["제주"],
    }
    text = f"{title} {org}"
    for region, keywords in regions.items():
        for kw in keywords:
            if kw in text:
                return region
    return "전국"


def detect_status(deadline_str):
    """마감일로 접수 상태 판단"""
    if not deadline_str or deadline_str in ["상시", "미정", ""]:
        return "상시접수"
    try:
        deadline = datetime.strptime(deadline_str, "%Y%m%d")
        days = (deadline - datetime.now()).days
        if days < 0:
            return "마감"
        elif days <= 14:
            return "마감임박"
        else:
            return "접수중"
    except:
        return "접수중"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 1: 기업마당 (bizinfo.go.kr)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_bizinfo():
    """기업마당 API에서 지원사업 공고 수집"""
    if not BIZINFO_API_KEY:
        print("⚠️  BIZINFO_API_KEY가 설정되지 않았습니다. 기업마당 API를 건너뜁니다.")
        return []

    programs = []
    url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

    for page in range(1, 6):  # 최대 5페이지
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "pageUnit": 50,
            "pageIndex": page,
            "searchSDate": THIRTY_DAYS_AGO,
            "searchEDate": TODAY,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("jsonArray", [])
            if not items:
                break

            for item in items:
                title = item.get("pblancNm", "").strip()
                org = item.get("jrsdInsttNm", "").strip()
                description = item.get("bsnsSumryCn", "").strip()
                deadline = item.get("reqstEndDe", "").strip().replace("-", "")
                detail_url = item.get("detailUrl", "")
                target = item.get("trgetNm", "").strip()

                if not title:
                    continue

                programs.append({
                    "title": title,
                    "org": org,
                    "category": classify_category(title, description),
                    "region": detect_region(title, org),
                    "amount": "공고문 참조",
                    "deadline": deadline if deadline else "상시",
                    "status": detect_status(deadline),
                    "description": description if description else f"{org}에서 진행하는 {title}",
                    "target": target if target else "공고문 참조",
                    "url": detail_url if detail_url else "https://www.bizinfo.go.kr",
                    "isNew": True,
                    "views": 0,
                    "source": "기업마당 API",
                    "verified": True,
                    "fetchDate": TODAY,
                })

            print(f"  📄 기업마당 페이지 {page}: {len(items)}건 수집")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ 기업마당 API 오류 (페이지 {page}): {e}")
            break

    return programs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 2: 공공데이터포털 보조금24 서비스 목록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_subsidy24():
    """복지로 중앙부처복지서비스 API에서 복지 정보 수집"""
    if not DATA_GO_KR_API_KEY:
        print("⚠️  DATA_GO_KR_API_KEY가 설정되지 않았습니다. 복지서비스 API를 건너뜁니다.")
        return []
    programs = []
    url = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001"
    for page in range(1, 4):
        params = {"ServiceKey": DATA_GO_KR_API_KEY, "numOfRows": 100, "pageNo": page}
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                print(f"  ❌ 복지서비스 API 오류: {resp.status_code}")
                break
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            items = root.findall('.//servList')
            if not items:
                items = root.findall('.//item')
            if not items:
                print(f"  ⚠️ 복지서비스 페이지 {page}: 데이터 없음")
                break
            for item in items:
                title = (item.findtext('servNm') or item.findtext('wlfareInfoNm') or '').strip()
                org = (item.findtext('jurMnofNm') or item.findtext('ministryNm') or '').strip()
                desc = (item.findtext('servDgst') or item.findtext('wlfareInfoOutline') or '').strip()
                target = (item.findtext('trgterIndvdlNm') or '').strip()
                svc_id = (item.findtext('servId') or '').strip()
                if not title:
                    continue
                detail_url = f"https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId={svc_id}" if svc_id else "https://www.bokjiro.go.kr"
                programs.append({
                    "title": title, "org": org if org else "보건복지부",
                    "category": classify_category(title, desc),
                    "region": detect_region(title, org),
                    "amount": "공고문 참조", "deadline": "상시", "status": "상시접수",
                    "description": desc[:200] if desc else f"{org} 복지서비스",
                    "target": target if target else "공고문 참조",
                    "url": detail_url,
                    "isNew": True, "views": 0,
                    "source": "복지로 API", "verified": True, "fetchDate": TODAY,
                })
            print(f"  📄 복지서비스 페이지 {page}: {len(items)}건 수집")
        except Exception as e:
            print(f"  ❌ 복지서비스 API 오류: {e}")
            break
    return programs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 3: 온통청년 (youthcenter.go.kr)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_youth():
    """온통청년 API에서 청년 정책 수집"""
    if not YOUTH_API_KEY:
        print("⚠️  YOUTH_API_KEY 미설정 → 온통청년 건너뜀")
        return []
    programs = []
    url = "https://www.youthcenter.go.kr/opi/youthPlcyList.do"
    biz_types = [("023010","일자리"),("023020","주거"),("023030","교육"),("023040","복지문화"),("023050","참여권리")]
    for biz_code, biz_name in biz_types:
        try:
            resp = requests.get(url, params={"openApiVlak":YOUTH_API_KEY,"display":30,"pageIndex":1,"bizTycdSel":biz_code}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("youthPolicy", [])
            cat_map = {"일자리":"employment","주거":"welfare","교육":"education","복지문화":"welfare","참여권리":"welfare"}
            for item in items:
                title = item.get("polyBizSjnm","").strip()
                if not title: continue
                org = item.get("cnsgNmor","온통청년").strip()
                desc = item.get("polyItcnCn","").strip()
                programs.append({
                    "title":title, "org":org, "category":cat_map.get(biz_name,"welfare"),
                    "region":detect_region(title,org), "amount":"공고문 참조",
                    "deadline":"상시", "status":"접수중",
                    "description":desc[:200] if desc else f"청년 {biz_name} 정책",
                    "target":item.get("ageInfo","청년"), "url":item.get("rqutUrla","") or item.get("rfcSiteUrla1","") or "https://www.youthcenter.go.kr",
                    "isNew":True, "views":0, "source":f"온통청년 ({biz_name})", "verified":True, "fetchDate":TODAY,
                })
            print(f"  📄 온통청년 [{biz_name}]: {len(items)}건")
        except Exception as e:
            print(f"  ❌ 온통청년 오류 [{biz_name}]: {e}")
    return programs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 4: HRD-Net 직업훈련 (고용24)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_hrdnet():
    """HRD-Net에서 주요 직업훈련 과정 정보 수집"""
    if not DATA_GO_KR_API_KEY:
        print("⚠️  DATA_GO_KR_API_KEY 필요 → HRD-Net 건너뜀")
        return []
    programs = []
    train_types = [("C0061","K-디지털트레이닝"),("C0054","국민내일배움카드"),("C0055","국가기간전략산업")]
    for tr_code, tr_name in train_types:
        try:
            url = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
            sd = f"{THIRTY_DAYS_AGO[:4]}-{THIRTY_DAYS_AGO[4:6]}-{THIRTY_DAYS_AGO[6:]}"
            ed = f"{TODAY[:4]}-{TODAY[4:6]}-{TODAY[6:]}"
            resp = requests.get(url, params={"authKey":DATA_GO_KR_API_KEY,"returnType":"JSON","outType":"1","pageNum":1,"pageSize":20,"srchTraStDt":sd,"srchTraEndDt":ed,"sort":"ASC","sortCol":"TRNG_BGDE","crseTracseSe":tr_code}, timeout=30)
            data = resp.json()
            items = data.get("srchList", data.get("resultList", []))
            if not isinstance(items, list): items = []
            for item in items:
                title = item.get("trprNm",item.get("subTitle","")).strip()
                if not title: continue
                inst = item.get("trainstCstNm",item.get("instNm","")).strip()
                addr = item.get("addr1","").strip()
                end_dt = item.get("traEndDate",item.get("trngEndde","")).replace("-","")
                cost = item.get("courseMan",item.get("courseMn",""))
                cost_str = f"훈련비 {int(cost):,}원" if cost else "공고문 참조"
                programs.append({
                    "title":f"[{tr_name}] {title}", "org":inst or "HRD-Net", "category":"education",
                    "region":detect_region(addr,inst), "amount":cost_str,
                    "deadline":end_dt if end_dt else "상시", "status":detect_status(end_dt),
                    "description":f"{tr_name} 과정. {inst} 운영." + (f" {addr}" if addr else ""),
                    "target":"국민내일배움카드 발급자", "url":"https://hrd.work24.go.kr",
                    "isNew":True, "views":0, "source":f"HRD-Net ({tr_name})", "verified":True, "fetchDate":TODAY,
                })
            print(f"  📄 HRD-Net [{tr_name}]: {len(items)}건")
        except Exception as e:
            print(f"  ❌ HRD-Net 오류 [{tr_name}]: {e}")
    return programs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 크롤링 5: 주요 지자체 지원사업
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_local_gov():
    """기업마당 API의 지역 필터로 주요 지자체 사업 수집"""
    if not BIZINFO_API_KEY:
        print("⚠️  BIZINFO_API_KEY 필요 → 지자체 수집 건너뜀")
        return []
    programs = []
    regions = [("대구","C055"),("서울","C011"),("부산","C021"),("경기","C031"),("경북","C053"),("인천","C023"),("광주","C025"),("대전","C042"),("경남","C056")]
    for region_name, region_code in regions:
        try:
            resp = requests.get("https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do",
                params={"crtfcKey":BIZINFO_API_KEY,"dataType":"json","pageUnit":15,"pageIndex":1,"areaCd":region_code,"searchSDate":THIRTY_DAYS_AGO,"searchEDate":TODAY}, timeout=30)
            resp.raise_for_status()
            items = resp.json().get("jsonArray", [])
            for item in items:
                title = item.get("pblancNm","").strip()
                if not title: continue
                org = item.get("jrsdInsttNm","").strip()
                desc = item.get("bsnsSumryCn","").strip()
                dl = item.get("reqstEndDe","").strip().replace("-","")
                programs.append({
                    "title":title, "org":org, "category":classify_category(title,desc),
                    "region":region_name, "amount":"공고문 참조",
                    "deadline":dl if dl else "상시", "status":detect_status(dl),
                    "description":desc[:200] if desc else f"{org} 지원사업",
                    "target":item.get("trgetNm","공고문 참조"),
                    "url":item.get("detailUrl","") or "https://www.bizinfo.go.kr",
                    "isNew":True, "views":0, "source":f"기업마당 ({region_name})", "verified":True, "fetchDate":TODAY,
                })
            print(f"  📄 지자체 [{region_name}]: {len(items)}건")
        except Exception as e:
            print(f"  ❌ 지자체 오류 [{region_name}]: {e}")
    return programs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 병합 및 중복 제거
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def merge_programs(new_programs, existing_programs):
    """새 데이터와 기존 데이터 병합, 중복 제거"""
    seen_titles = set()
    merged = []

    # 새 데이터 우선
    for p in new_programs:
        normalized = re.sub(r'\s+', '', p["title"])
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            merged.append(p)

    # 기존 데이터 중 겹치지 않는 것만 추가 (최근 60일 이내)
    cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
    for p in existing_programs:
        normalized = re.sub(r'\s+', '', p["title"])
        fetch_date = p.get("fetchDate", "20260101")
        if normalized not in seen_titles and fetch_date >= cutoff:
            p["isNew"] = False
            seen_titles.add(normalized)
            merged.append(p)

    # ID 재부여
    for i, p in enumerate(merged):
        p["id"] = i + 1

    return merged


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HTML 대시보드 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_html(programs):
    """수집된 데이터로 대시보드 HTML 생성"""

    programs_json = json.dumps(programs, ensure_ascii=False)
    update_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    # template.html은 scripts/ 폴더의 상위(프로젝트 루트)에 있음
    template_path = Path(__file__).parent.parent / "template.html"
    if not template_path.exists():
        # scripts/ 같은 폴더에도 확인
        template_path = Path(__file__).parent / "template.html"

    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        html = template.replace("__PROGRAMS_DATA__", programs_json)
        return html
    else:
        print("⚠️  template.html을 찾을 수 없습니다. 인라인 HTML을 생성합니다.")
        return generate_inline_html(programs, update_time)


def generate_inline_html(programs, update_time):
    """인라인 HTML 대시보드 생성 (template.html이 없을 때)"""
    programs_json = json.dumps(programs, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 정부 지원금 통합 안내 대시보드</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#F0F2F7;--sf:#FFF;--sa:#F7F8FB;--ik:#0D1B2A;--ik2:#3D5A80;--ik3:#8DA2B8;--bl:#2563EB;--bd:#E2E8F0;--bl2:#EFF2F7; }}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans KR',-apple-system,sans-serif;background:var(--bg);color:var(--ik);line-height:1.6}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes drift{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}
.anim{{animation:fadeUp .45s cubic-bezier(.22,1,.36,1) both}}
.hdr{{background:linear-gradient(160deg,#0D1B2A,#1B2D45 60%,#243B55);padding:26px 0 22px;position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.15)}}
.hdr-in{{max-width:1220px;margin:0 auto;padding:0 28px;display:flex;justify-content:space-between;align-items:center}}
.hdr-t{{font-size:23px;font-weight:900;color:#fff;letter-spacing:-.04em;display:flex;align-items:center;gap:12px}}
.hdr-t em{{font-style:normal;color:#60A5FA}}
.hdr-sub{{font-size:12px;color:#7B9BBF;margin-top:2px}}
.hdr-st{{display:flex;align-items:center;gap:8px;padding:8px 16px;border-radius:8px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08)}}
.hdr-n{{font-size:20px;font-weight:900;color:#60A5FA}}
.hdr-l{{font-size:12px;color:#7B9BBF}}
.main{{max-width:1220px;margin:0 auto;padding:28px 28px 80px}}
.vb{{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:100px;font-size:11px;font-weight:600;background:#DCFCE7;color:#166534;border:1px solid #BBF7D0;margin-bottom:16px}}
.fb{{background:var(--sf);border-radius:20px;padding:22px 26px;margin-bottom:24px;border:1px solid var(--bd)}}
.sw{{position:relative;margin-bottom:16px}}
.si{{position:absolute;left:15px;top:50%;transform:translateY(-50%);font-size:16px}}
.sinp{{width:100%;padding:13px 18px 13px 44px;border-radius:12px;border:1.5px solid var(--bd);font-size:14px;outline:none;background:var(--sa);color:var(--ik);font-family:inherit}}
.sinp:focus{{border-color:var(--bl);background:#fff}}
.sinp::placeholder{{color:var(--ik3)}}
.cr{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}}
.cb{{padding:7px 15px;border-radius:100px;font-size:12.5px;font-weight:600;cursor:pointer;border:1.5px solid var(--bd);background:#fff;color:var(--ik2);font-family:inherit;transition:all .2s}}
.cb.on{{border-color:var(--ac);background:var(--abg);color:var(--ac)}}
.fr{{display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
.fs{{padding:8px 14px;border-radius:10px;border:1px solid var(--bd);font-size:13px;color:var(--ik2);background:var(--sa);cursor:pointer;outline:none;font-family:inherit}}
.fc{{font-size:13px;color:var(--ik3);margin-left:auto}}
.fc strong{{color:var(--bl)}}
.cg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:18px}}
.cd{{background:var(--sf);border-radius:14px;padding:24px;cursor:pointer;position:relative;border:1px solid var(--bl2);overflow:hidden;transition:all .3s cubic-bezier(.22,1,.36,1)}}
.cd:hover{{transform:translateY(-4px);box-shadow:0 8px 30px rgba(13,27,42,.07)}}
.ca{{position:absolute;top:0;left:0;right:0;height:3px}}
.ct{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}}
.ctl{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.tc{{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:100px;font-size:11px;font-weight:600}}
.tr{{padding:3px 8px;border-radius:100px;font-size:11px;font-weight:500;background:#F1F5F9;color:#475569}}
.tn{{padding:3px 8px;border-radius:100px;font-size:10px;font-weight:700;background:#DC2626;color:#fff}}
.sb{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:100px;font-size:11px;font-weight:600}}
.s-a{{background:#DCFCE7;color:#166534;border:1px solid #BBF7D0}}
.s-w{{background:#DBEAFE;color:#1E40AF;border:1px solid #BFDBFE}}
.s-u{{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A}}
.s-c{{background:#F3F4F6;color:#6B7280;border:1px solid #E5E7EB}}
.ctt{{font-size:17px;font-weight:700;line-height:1.4;margin-bottom:6px}}
.co{{font-size:13px;color:var(--ik3);font-weight:500;margin-bottom:10px}}
.cds{{font-size:13.5px;color:var(--ik2);line-height:1.6;margin-bottom:16px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.cf{{display:flex;justify-content:space-between;align-items:center;padding-top:14px;border-top:1px solid var(--bl2)}}
.cm{{display:flex;gap:14px;font-size:12.5px;color:var(--ik3)}}
.cma{{font-weight:600;color:var(--ik)}}
.dd{{font-size:11px;font-weight:700}}
.dd-u{{color:#DC2626}}.dd-s{{color:#D97706}}
.src{{font-size:10px;color:var(--ik3);margin-top:8px;display:flex;align-items:center;gap:4px}}
.src-v{{display:inline-block;width:6px;height:6px;border-radius:50%;background:#059669}}
.emp{{text-align:center;padding:60px 20px;background:var(--sf);border-radius:14px;border:1px solid var(--bl2);grid-column:1/-1}}
.mo{{position:fixed;inset:0;background:rgba(0,0,0,.5);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;z-index:1000;padding:20px}}
.mo.h{{display:none}}
.ml{{background:var(--sf);border-radius:20px;max-width:620px;width:100%;max-height:85vh;overflow:auto;padding:36px;box-shadow:0 20px 50px rgba(13,27,42,.12);animation:fadeUp .3s cubic-bezier(.22,1,.36,1)}}
.mh{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px}}
.mt{{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}}
.mtt{{font-size:22px;font-weight:800;line-height:1.3}}
.mx{{background:var(--sa);border:none;border-radius:50%;width:38px;height:38px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;color:var(--ik2);flex-shrink:0;margin-left:14px}}
.mg{{background:var(--sa);border-radius:14px;padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.ml2{{font-size:11px;color:var(--ik3);font-weight:600;margin-bottom:3px}}
.mv{{font-size:14px;font-weight:600}}
.ms{{margin-bottom:20px}}
.ms h4{{font-size:14px;font-weight:700;margin-bottom:8px}}
.ms p{{font-size:14px;color:var(--ik2);line-height:1.7}}
.mc{{width:100%;padding:15px;border-radius:12px;color:#fff;border:none;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:16px}}
.mc:hover{{transform:scale(1.015)}}
.info{{margin-top:32px;padding:20px 24px;background:var(--sf);border-radius:14px;border:1px solid var(--bd)}}
.info h4{{font-size:14px;font-weight:700;margin-bottom:8px}}
.info p{{font-size:13px;color:var(--ik3);line-height:1.7}}
@media(max-width:768px){{.hdr-in{{flex-direction:column;gap:12px;align-items:flex-start}}.cg{{grid-template-columns:1fr}}.ml{{padding:24px}}.mg{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="hdr"><div class="hdr-in"><div><div class="hdr-t"><span style="font-size:30px;animation:drift 3.5s ease-in-out infinite">🏛</span>2026 정부 지원금 <em>통합 안내</em></div><p class="hdr-sub">자동 업데이트 | {update_time} 기준</p></div><div class="hdr-st"><span class="hdr-l">총</span><span class="hdr-n">{len(programs)}</span><span class="hdr-l">건</span></div></div></header>
<main class="main">
<div class="vb">✅ 공공데이터 API 기반 자동 수집 · {update_time} 업데이트</div>
<div class="fb"><div class="sw"><span class="si">🔍</span><input class="sinp" id="searchInp" placeholder="지원사업명, 기관명, 키워드로 검색..." oninput="render()"/></div><div class="cr" id="catRow"></div><div class="fr"><select class="fs" id="regionSel" onchange="render()"></select><select class="fs" id="sortSel" onchange="render()"><option value="latest">🕐 최신순</option><option value="deadline">⏰ 마감임박순</option><option value="popular">🔥 인기순</option></select><span class="fc">검색결과 <strong id="fCnt">0</strong>건</span></div></div>
<div class="cg" id="grid"></div>
<div class="info"><h4>ℹ️ 자동 업데이트 안내</h4><p>이 대시보드는 GitHub Actions를 통해 매일 자동으로 기업마당·보조금24 API에서 최신 지원사업 정보를 수집합니다. 마지막 업데이트: {update_time}. 실제 신청 전 반드시 해당 기관 공식 홈페이지에서 세부 요건을 확인하세요.</p></div>
</main>
<div class="mo h" id="mO" onclick="closeM(event)"><div class="ml" id="mC" onclick="event.stopPropagation()"></div></div>
<script>
const CATS=[{{id:"all",label:"전체",icon:"📋",color:"#2563EB"}},{{id:"small_biz",label:"소상공인",icon:"🏪",color:"#D97706"}},{{id:"startup",label:"창업지원",icon:"🚀",color:"#7C3AED"}},{{id:"employment",label:"고용/취업",icon:"💼",color:"#059669"}},{{id:"tech",label:"기술/R&D",icon:"🔬",color:"#DB2777"}},{{id:"agriculture",label:"농림/수산",icon:"🌾",color:"#65A30D"}},{{id:"welfare",label:"복지/생활",icon:"🏠",color:"#0891B2"}},{{id:"education",label:"교육/훈련",icon:"📚",color:"#EA580C"}}];
const REGS=["전국","서울","부산","대구","인천","광주","대전","울산","세종","경기","강원","충북","충남","전북","전남","경북","경남","제주"];
const P={programs_json};
let selCat="all";
function fmtD(d){{if(!d||["상시","미정","공고문 참조","세부사업별 상이","사업별 상이","예산 소진시","추후 공고"].includes(d))return d;try{{const dt=new Date(d.replace(/(\\d{{4}})(\\d{{2}})(\\d{{2}})/,"$1-$2-$3"));return `${{dt.getFullYear()}}.${{String(dt.getMonth()+1).padStart(2,'0')}}.${{String(dt.getDate()).padStart(2,'0')}}`}}catch{{return d}}}}
function dL(d){{if(!d||["상시","미정","공고문 참조","세부사업별 상이","사업별 상이","예산 소진시","추후 공고"].includes(d))return null;try{{const dt=new Date(d.replace(/(\\d{{4}})(\\d{{2}})(\\d{{2}})/,"$1-$2-$3"));return Math.ceil((dt-new Date())/864e5)}}catch{{return null}}}}
function cOf(id){{return CATS.find(c=>c.id===id)||CATS[0]}}
function sC(s){{return s==="접수중"?"s-a":s==="상시접수"?"s-w":s==="마감임박"?"s-u":"s-c"}}
function init(){{const cr=document.getElementById("catRow");CATS.forEach(c=>{{const b=document.createElement("button");b.className="cb"+(c.id==="all"?" on":"");b.textContent=`${{c.icon}} ${{c.label}}`;b.style.setProperty("--ac",c.color);b.style.setProperty("--abg",c.color+"14");b.onclick=()=>{{selCat=c.id;document.querySelectorAll(".cb").forEach(x=>x.classList.remove("on"));b.classList.add("on");render()}};cr.appendChild(b)}});const rs=document.getElementById("regionSel");REGS.forEach(r=>{{const o=document.createElement("option");o.value=r;o.textContent=`📍 ${{r}}`;rs.appendChild(o)}});render()}}
function render(){{const q=document.getElementById("searchInp").value.toLowerCase(),rg=document.getElementById("regionSel").value,so=document.getElementById("sortSel").value;let f=P.filter(p=>{{const c1=selCat==="all"||p.category===selCat,c2=rg==="전국"||p.region===rg||p.region==="전국",c3=!q||p.title.toLowerCase().includes(q)||p.org.toLowerCase().includes(q)||p.description.toLowerCase().includes(q);return c1&&c2&&c3}});f.sort((a,b)=>{{if(so==="latest")return(b.isNew-a.isNew)||(b.id-a.id);if(so==="popular")return(b.views||0)-(a.views||0);return 0}});document.getElementById("fCnt").textContent=f.length;const g=document.getElementById("grid");if(!f.length){{g.innerHTML='<div class="emp"><div style="font-size:48px;margin-bottom:16px">🔍</div><div style="font-size:18px;font-weight:700">검색 결과가 없습니다</div></div>';return}}g.innerHTML=f.map((p,i)=>{{const c=cOf(p.category),dl=dL(p.deadline);let dd="";if(dl!==null&&dl>0&&dl<=30)dd=`<span class="dd ${{dl<=7?'dd-u':'dd-s'}}">D-${{dl}}</span>`;return`<div class="cd anim" style="animation-delay:${{i*.03}}s" onclick='openM(${{p.id}})'><div class="ca" style="background:linear-gradient(90deg,${{c.color}},${{c.color}}88)"></div><div class="ct"><div class="ctl"><span class="tc" style="background:${{c.color}}14;color:${{c.color}}">${{c.icon}} ${{c.label}}</span>${{p.region!=="전국"?`<span class="tr">📍 ${{p.region}}</span>`:""}}${{p.isNew?'<span class="tn">NEW</span>':""}}</div><span class="sb ${{sC(p.status)}}">${{p.status}}</span></div><div class="ctt">${{p.title}}</div><div class="co">${{p.org}}</div><div class="cds">${{p.description}}</div><div class="cf"><div class="cm"><span class="cma">💰 ${{p.amount}}</span><span>📅 ${{fmtD(p.deadline)}}</span></div>${{dd}}</div>${{p.source?`<div class="src"><span class="src-v"></span>출처: ${{p.source}}</div>`:""}}</div>`}}).join("")}}
function openM(id){{const p=P.find(x=>x.id===id);if(!p)return;const c=cOf(p.category);document.getElementById("mC").innerHTML=`<div class="mh"><div style="flex:1"><div class="mt"><span class="tc" style="background:${{c.color}}14;color:${{c.color}};padding:4px 12px;font-size:12px">${{c.icon}} ${{c.label}}</span><span class="sb ${{sC(p.status)}}" style="font-size:12px">${{p.status}}</span></div><div class="mtt">${{p.title}}</div></div><button class="mx" onclick="closeM()">✕</button></div><div class="mg"><div><div class="ml2">🏛 지원기관</div><div class="mv">${{p.org}}</div></div><div><div class="ml2">💰 지원금액</div><div class="mv">${{p.amount}}</div></div><div><div class="ml2">📅 신청마감</div><div class="mv">${{fmtD(p.deadline)}}</div></div><div><div class="ml2">📍 지원지역</div><div class="mv">${{p.region}}</div></div></div><div class="ms"><h4>📝 사업 개요</h4><p>${{p.description}}</p></div><div class="ms"><h4>🎯 지원 대상</h4><p>${{p.target}}</p></div><button class="mc" style="background:linear-gradient(135deg,${{c.color}},${{c.color}}CC);box-shadow:0 4px 16px ${{c.color}}40" onclick="window.open('${{p.url}}','_blank')">공식 페이지에서 상세정보 확인 →</button>`;document.getElementById("mO").classList.remove("h");document.body.style.overflow="hidden"}}
function closeM(e){{if(e&&e.target!==e.currentTarget)return;document.getElementById("mO").classList.add("h");document.body.style.overflow=""}}
init();
</script>
</body>
</html>"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    print(f"\n🏛  정부 지원금 자동 수집 시작 ({TODAY})")
    print("=" * 50)

    # 1) 기존 데이터 로드
    existing = []
    if DATA_FILE.exists():
        try:
            existing = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            print(f"📂 기존 데이터: {len(existing)}건")
        except:
            existing = []

    # 2) API에서 새 데이터 수집
    print("\n📡 API 데이터 수집 중...")
    new_programs = []

    print("\n[1/5] 기업마당 API")
    new_programs.extend(fetch_bizinfo())

    print("\n[2/5] 보조금24 API")
    new_programs.extend(fetch_subsidy24())

    print("\n[3/5] 온통청년 API")
    new_programs.extend(fetch_youth())

    print("\n[4/5] HRD-Net 직업훈련 API")
    new_programs.extend(fetch_hrdnet())

    print("\n[5/5] 지자체 지원사업")
    new_programs.extend(fetch_local_gov())

    print(f"\n📊 새로 수집: {len(new_programs)}건")

    # 3) 데이터 병합
    if new_programs:
        merged = merge_programs(new_programs, existing)
    else:
        print("⚠️  새 데이터가 없어 기존 데이터를 유지합니다.")
        merged = existing if existing else []

    # 4) 저장
    DATA_FILE.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"💾 data.json 저장: {len(merged)}건")

    # 5) HTML 생성
    html = generate_html(merged)
    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"🌐 index.html 생성 완료")

    print(f"\n✅ 완료! 총 {len(merged)}건 ({TODAY})")
    print("=" * 50)


if __name__ == "__main__":
    main()
