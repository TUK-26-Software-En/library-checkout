"""
pyreverse(pylint) + graphviz 를 사용해 코드 기반 UML 다이어그램을 생성한다.

생성 대상:
  1. class_diagram.png   — 전체 클래스 다이어그램 (models + services + repositories)
  2. package_diagram.png — 패키지(모듈) 의존성 다이어그램
  3. er_diagram.png      — SQLAlchemy ORM 모델 ER 다이어그램
"""

import subprocess
import sys
from pathlib import Path
import graphviz

ROOT = Path(__file__).parent
APP = ROOT / "app"
OUT = ROOT / "docx" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

PYREVERSE = ROOT / ".venv" / "bin" / "pyreverse"


# ── 1. pyreverse: Class Diagram ───────────────────────────────────────────────

def run_pyreverse_class():
    """models / services / repositories 대상 클래스 다이어그램"""
    targets = [
        str(APP / "models"),
        str(APP / "services"),
        str(APP / "repositories"),
    ]
    result = subprocess.run(
        [
            str(PYREVERSE),
            "--output", "dot",
            "--project", "library",
            "--colorized",
            *targets,
        ],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if result.returncode != 0:
        print("[WARN] pyreverse stderr:", result.stderr[:300])

    dot_path = ROOT / "classes_library.dot"
    if not dot_path.exists():
        print("[ERROR] classes_library.dot 생성 실패")
        print(result.stdout, result.stderr)
        return

    src = graphviz.Source(dot_path.read_text())
    src.render(
        filename=str(OUT / "class_diagram"),
        format="png",
        cleanup=True,
    )
    dot_path.unlink(missing_ok=True)
    print(f"[OK] class_diagram.png → {OUT / 'class_diagram.png'}")


# ── 2. pyreverse: Package Diagram ─────────────────────────────────────────────

def run_package_diagram():
    """
    실제 import 관계를 기반으로 패키지 다이어그램을 작성한다.
    pyreverse 는 개별 모듈까지 모두 노출해 엣지가 교차하므로,
    graphviz DOT 로 직접 기술한다.

    레이어 구성 (TB, rank 고정):
      main ─ database
      ├─ Presentation  : routers
      ├─ Business      : services
      └─ Data          : repositories + models
    """
    dot_src = r"""
digraph PackageDiagram {
    graph [rankdir=TB, fontname="Helvetica", fontsize=12,
           nodesep=0.6, ranksep=0.9, splines=ortho, pad=0.5]
    node  [fontname="Helvetica", fontsize=11, style="filled,rounded",
           shape=box, width=1.6, height=0.45]
    edge  [fontname="Helvetica", fontsize=9, color="#444444"]

    /* ── 공통 노드 ────────────────────────────────── */
    main     [label="main.py",     fillcolor="#D5D8DC"]
    database [label="database.py", fillcolor="#D5D8DC", shape=cylinder,
              height=0.6]

    /* ── Presentation Layer ──────────────────────── */
    subgraph cluster_routers {
        label="app.routers  [ Presentation Layer ]"
        style="filled,rounded"
        fillcolor="#D6EAF8"
        color="#2980B9"
        fontcolor="#1A5276"
        fontsize=12

        book_router   [label="book_router",   fillcolor="#AED6F1"]
        member_router [label="member_router", fillcolor="#AED6F1"]
        loan_router   [label="loan_router",   fillcolor="#AED6F1"]
    }

    /* ── Business Layer ──────────────────────────── */
    subgraph cluster_services {
        label="app.services  [ Business Layer ]"
        style="filled,rounded"
        fillcolor="#D5F5E3"
        color="#1E8449"
        fontcolor="#1D6A3F"
        fontsize=12

        book_service   [label="book_service",   fillcolor="#A9DFBF"]
        member_service [label="member_service", fillcolor="#A9DFBF"]
        loan_service   [label="loan_service",   fillcolor="#A9DFBF"]
    }

    /* ── Data Layer : Repositories ───────────────── */
    subgraph cluster_repos {
        label="app.repositories  [ Data Layer ]"
        style="filled,rounded"
        fillcolor="#FDEBD0"
        color="#CA6F1E"
        fontcolor="#784212"
        fontsize=12

        book_repo   [label="book_repository",   fillcolor="#FAD7A0"]
        member_repo [label="member_repository", fillcolor="#FAD7A0"]
        loan_repo   [label="loan_repository",   fillcolor="#FAD7A0"]
    }

    /* ── Data Layer : Models ─────────────────────── */
    subgraph cluster_models {
        label="app.models  [ Data Layer ]"
        style="filled,rounded"
        fillcolor="#F9EBEA"
        color="#B03A2E"
        fontcolor="#7B241C"
        fontsize=12

        book_model   [label="book.py",   fillcolor="#F1948A"]
        member_model [label="member.py", fillcolor="#F1948A"]
        loan_model   [label="loan.py",   fillcolor="#F1948A"]
    }

    /* ── rank 고정 ───────────────────────────────── */
    { rank=same; main; database }
    { rank=same; book_router; member_router; loan_router }
    { rank=same; book_service; member_service; loan_service }
    { rank=same; book_repo; member_repo; loan_repo }
    { rank=same; book_model; member_model; loan_model }

    /* ── main ──────────────────────────────────────── */
    main -> database       [style=dashed, arrowhead=open]
    main -> book_router    [style=dashed, arrowhead=open]
    main -> member_router  [style=dashed, arrowhead=open]
    main -> loan_router    [style=dashed, arrowhead=open]

    /* ── routers → services ──────────────────────── */
    book_router   -> book_service                        [weight=5]
    member_router -> member_service                      [weight=5]
    loan_router   -> book_service                        [weight=3]
    loan_router   -> member_service                      [weight=3]
    loan_router   -> loan_service                        [weight=5]

    /* ── routers → database (get_db) ─────────────── */
    book_router   -> database [style=dashed, arrowhead=open, color="#AAAAAA"]
    member_router -> database [style=dashed, arrowhead=open, color="#AAAAAA"]
    loan_router   -> database [style=dashed, arrowhead=open, color="#AAAAAA"]

    /* ── services → repositories ─────────────────── */
    book_service   -> book_repo                          [weight=5]
    member_service -> member_repo                        [weight=5]
    loan_service   -> book_repo                          [weight=3]
    loan_service   -> member_repo                        [weight=3]
    loan_service   -> loan_repo                          [weight=5]

    /* ── services → models ───────────────────────── */
    book_service   -> book_model   [style=dashed, arrowhead=open]
    member_service -> member_model [style=dashed, arrowhead=open]
    loan_service   -> loan_model   [style=dashed, arrowhead=open]

    /* ── repositories → models ───────────────────── */
    book_repo   -> book_model                            [weight=5]
    member_repo -> member_model                          [weight=5]
    loan_repo   -> loan_model                            [weight=5]

    /* ── models → database ───────────────────────── */
    book_model   -> database                             [weight=5]
    member_model -> database                             [weight=5]
    loan_model   -> database                             [weight=5]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "package_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] package_diagram.png → {OUT / 'package_diagram.png'}")


# ── 3. graphviz: ER Diagram (SQLAlchemy 모델 수동 반영) ──────────────────────

def run_er_diagram():
    """
    SQLAlchemy ORM 모델 3개(Book / Member / Loan)의 관계를
    graphviz DOT로 직접 기술해 ER 다이어그램을 생성한다.
    pyreverse는 ORM 관계를 해석하지 못하므로 별도로 작성한다.
    """
    dot_src = """
digraph ER {
    graph [rankdir=LR, fontname="Helvetica", splines=ortho]
    node  [shape=record, fontname="Helvetica", fontsize=11]
    edge  [fontname="Helvetica", fontsize=10]

    Book [label="{Book|id : INTEGER PK\\ltitle : VARCHAR\\lauthor : VARCHAR\\lpublisher : VARCHAR\\lavailable : BOOLEAN\\l}"]
    Member [label="{Member|id : INTEGER PK\\lname : VARCHAR\\lemail : VARCHAR UNIQUE\\l}"]
    Loan [label="{Loan|id : INTEGER PK\\lbook_id : INTEGER FK\\lmember_id : INTEGER FK\\lloan_date : DATE\\lreturn_date : DATE\\lstatus : ENUM(ACTIVE,RETURNED)\\l}"]

    Book -> Loan [label="1 : N", arrowhead=crow, arrowtail=none, dir=both]
    Member -> Loan [label="1 : N", arrowhead=crow, arrowtail=none, dir=both]
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "er_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] er_diagram.png → {OUT / 'er_diagram.png'}")


# ── 4. graphviz: 3 Layer Architecture Diagram ────────────────────────────────

def run_layer_diagram():
    dot_src = """
digraph LayerArch {
    graph [rankdir=TB, fontname="Helvetica", splines=ortho, nodesep=0.5]
    node  [fontname="Helvetica", fontsize=11, style=filled]
    edge  [fontname="Helvetica", fontsize=10]

    subgraph cluster_presentation {
        label="Presentation Layer"
        style=filled; fillcolor="#D6EAF8"
        Templates [label="Jinja2 Templates\\n(View)", fillcolor="#AED6F1"]
        Routers   [label="book_router\\nmember_router\\nloan_router", fillcolor="#AED6F1"]
    }

    subgraph cluster_business {
        label="Business Layer"
        style=filled; fillcolor="#D5F5E3"
        BookSvc   [label="BookService",   fillcolor="#A9DFBF"]
        MemberSvc [label="MemberService", fillcolor="#A9DFBF"]
        LoanSvc   [label="LoanService",   fillcolor="#A9DFBF"]
    }

    subgraph cluster_data {
        label="Data Layer"
        style=filled; fillcolor="#FDEBD0"
        BookRepo   [label="BookRepository",   fillcolor="#FAD7A0"]
        MemberRepo [label="MemberRepository", fillcolor="#FAD7A0"]
        LoanRepo   [label="LoanRepository",   fillcolor="#FAD7A0"]
        DB         [label="SQLite DB", shape=cylinder, fillcolor="#E59866"]
    }

    User [label="User / Admin", shape=ellipse, fillcolor="#D7BDE2"]

    User     -> Templates
    Templates -> Routers
    Routers  -> BookSvc
    Routers  -> MemberSvc
    Routers  -> LoanSvc
    BookSvc   -> BookRepo
    MemberSvc -> MemberRepo
    LoanSvc   -> BookRepo
    LoanSvc   -> MemberRepo
    LoanSvc   -> LoanRepo
    BookRepo   -> DB
    MemberRepo -> DB
    LoanRepo   -> DB
}
"""
    src = graphviz.Source(dot_src)
    src.render(
        filename=str(OUT / "layer_diagram"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] layer_diagram.png → {OUT / 'layer_diagram.png'}")


# ── 5. graphviz: Sequence Diagram (대출 흐름) ─────────────────────────────────

def run_sequence_diagram():
    """
    graphviz로 시퀀스 다이어그램을 표현한다.
    참가자(lifeline)를 열로, 각 메시지를 행(rank)으로 배치해
    UML 시퀀스 다이어그램과 유사한 레이아웃을 구성한다.
    """
    actors = ["User", "LoanRouter", "LoanService", "BookRepository", "LoanRepository", "SQLite_DB"]
    labels = {
        "User":           "User",
        "LoanRouter":     "LoanRouter",
        "LoanService":    "LoanService",
        "BookRepository": "BookRepository",
        "LoanRepository": "LoanRepository",
        "SQLite_DB":      "SQLite DB",
    }
    colors = {
        "User":           "#D7BDE2",
        "LoanRouter":     "#AED6F1",
        "LoanService":    "#A9DFBF",
        "BookRepository": "#FAD7A0",
        "LoanRepository": "#FAD7A0",
        "SQLite_DB":      "#F9E79F",
    }

    messages = [
        ("User",           "LoanRouter",     "POST /loans/new\\n(member_id, book_id)", False),
        ("LoanRouter",     "LoanService",    "borrow_book(member_id, book_id)", False),
        ("LoanService",    "BookRepository", "find_by_id(book_id)", False),
        ("BookRepository", "SQLite_DB",      "SELECT * FROM books", False),
        ("SQLite_DB",      "BookRepository", "Book", True),
        ("BookRepository", "LoanService",    "Book", True),
        ("LoanService",    "BookRepository", "save(book, available=False)", False),
        ("BookRepository", "SQLite_DB",      "UPDATE books SET available=0", False),
        ("LoanService",    "LoanRepository", "save(Loan, status=ACTIVE)", False),
        ("LoanRepository", "SQLite_DB",      "INSERT INTO loans", False),
        ("LoanService",    "LoanRouter",     "Loan", True),
        ("LoanRouter",     "User",           "303 Redirect /loans/", True),
    ]

    # 열 위치
    col = {a: i for i, a in enumerate(actors)}
    n_cols = len(actors)
    n_rows = len(messages)
    col_w, row_h = 2.2, 0.7

    lines = ['digraph Seq {']
    lines += ['  graph [rankdir=TB, splines=false, nodesep=0, ranksep=0, pad=0.4]']
    lines += ['  node  [shape=box, style=filled, fontname="Helvetica", fontsize=10]']
    lines += ['  edge  [fontname="Helvetica", fontsize=9]']

    # ── 헤더 노드 ──────────────────────────────────────────────
    for a in actors:
        x = col[a] * col_w
        lines.append(
            f'  H_{a} [label="{labels[a]}", fillcolor="{colors[a]}",'
            f' pos="{x},0!", width=1.8, height=0.5]'
        )

    # ── lifeline 점선 ──────────────────────────────────────────
    for a in actors:
        x = col[a] * col_w
        for r in range(n_rows + 1):
            y = -(r + 0.8) * row_h
            lines.append(
                f'  L_{a}_{r} [shape=point, width=0.01, style=invis,'
                f' pos="{x},{y}!"]'
            )
        # lifeline edge (점선)
        for r in range(n_rows):
            lines.append(
                f'  L_{a}_{r} -> L_{a}_{r+1}'
                f' [style=dashed, arrowhead=none, color="#AAAAAA"]'
            )

    # ── 메시지 화살표 ──────────────────────────────────────────
    for r, (frm, to, lbl, ret) in enumerate(messages):
        style = 'dashed' if ret else 'solid'
        arrow = 'open' if ret else 'normal'
        lines.append(
            f'  L_{frm}_{r} -> L_{to}_{r}'
            f' [label="{lbl}", style={style}, arrowhead={arrow},'
            f' color="{"#555555" if ret else "#1A5276"}"]'
        )

    lines.append('}')
    dot_src = '\n'.join(lines)

    src = graphviz.Source(dot_src, engine="neato")
    src.render(
        filename=str(OUT / "sequence_borrow"),
        format="png",
        cleanup=True,
    )
    print(f"[OK] sequence_borrow.png → {OUT / 'sequence_borrow.png'}")


if __name__ == "__main__":
    print("=== UML 다이어그램 생성 시작 (pyreverse + graphviz) ===\n")
    run_pyreverse_class()
    run_package_diagram()
    run_er_diagram()
    run_layer_diagram()
    run_sequence_diagram()
    print(f"\n=== 완료 — 출력 위치: {OUT} ===")
