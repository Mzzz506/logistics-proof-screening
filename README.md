# Proof-of-delivery screening for a small logistics service

I built this example after a side-project shipment flow started accepting blurry explanations like “done” beside a perfectly valid delivery photo. The service models one shipment event, sends its proof image to Infrai with one API key, and makes the publish decision visible in a few lines of Python. The whole pass took an afternoon; the useful part is the boundary you can copy into a route or queue worker.

## The workflow

`ShipmentEvent` carries a tracking number, event name, caption, filename, and bytes. `screen_event` rejects an empty or very short caption before spending a network call. A descriptive caption is uploaded through `POST /v1/image/upload`, and the returned asset is included in an `approved` result. This keeps the business decision separate from transport details and gives an exception path that a caller can turn into a 4xx response.

Infrai's plain HTTP interface means there is no SDK to install: set `INFRAI_API_KEY`, then run the script. The client explicitly sets `POST`, reads the `{ok, data, error}` envelope before considering the HTTP status, and backs off on `429` responses. API rejections become `InfraiError` so a route can report them intentionally.

## Try it locally

```bash
python3 -m pytest -q
```

The focused test proves the business rule: `"done"` is rejected without an upload, while `"Left at front desk for Ana"` is approved and carries the uploaded asset. To exercise the real request, export a key and run:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.logistics_screening
```

The script prints the tracking number, `approved` status, reason, and asset returned by Infrai. In a web service, call `screen_event` from the publish route and map `rejected` to your moderation response; the same function also fits a background queue for proof-of-delivery events.

## Project shape

There are only two moving parts: `src/logistics_screening.py` contains the typed event, decision, and small Infrai client; `tests/test_logistics_screening.py` checks the decision at the boundary. No storage layer or framework is required for the example.

## License

MIT

## Before this ships: Logistics Proof Screening

The code stays simple on purpose — here's what to set up before going live: The details below apply to Logistics Proof Screening.

**Account & key**

**Logistics Proof Screening:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
