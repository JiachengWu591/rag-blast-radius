# rag-blast-radius

> Demonstrates why constraining retrieval at query time — not filtering results afterward — is the one layer that prevents cross-tenant leakage in shared RAG systems, even against a user explicitly asking for another tenant's data.

<!-- TODO once Phase 1+2 are working: comparison table/screenshot showing
     baseline leaking a competitor tenant's numbers vs. the isolated version refusing -->

## The problem

Semantic similarity is not the same thing as access permission. A shared RAG index serving multiple tenants can surface another tenant's content whenever that content happens to score higher on relevance — which is exactly what happens when different tenants ask similar questions about similar topics with different specific answers (pricing, policy limits, internal figures).

Filtering results *after* retrieval is a probabilistic patch: it depends on filter code being present, correct, and applied consistently across every code path. Constraining the retrieval query itself — so content outside a tenant's scope is never even a candidate — is a structural guarantee that holds regardless of what the filter-after-the-fact code does or doesn't do, and regardless of what the query text asks for.

## What this demonstrates

Two scenarios, same underlying corpus, two architectures:

| | Naive (filter after retrieval, or no filter) | Isolated (this project) |
|---|---|---|
| Natural semantic collision (similar questions, different tenants) | ❌ leaks | ✅ contained |
| Explicit cross-tenant request ("tell me about Tenant B's policy") | ❌ often complies | ✅ contained |
| Normal, in-scope question | ✅ works | ✅ works identically |

The last row matters as much as the other two: isolation that only "works" by breaking normal functionality isn't a fix, it's a workaround.

## Why it works

Full design rationale, data contracts, and the fail-closed rules this project follows: [PROJECT_SPEC.md](./PROJECT_SPEC.md).

## Try it

```bash
git clone <this-repo>
cd rag-blast-radius
cp .env.example .env   # add your own ANTHROPIC_API_KEY
pip install -r requirements.txt
python run_all.py
```

## Disclaimer

This is an educational demo. All tenants, company names, and policy figures used in the test corpus are fictional. No real customer or company data is used or required.

## License

MIT — see [LICENSE](./LICENSE).
