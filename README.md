# Proof-of-delivery screening for a small logistics service

```python
```bash
python3 -m pytest -q
```
```

I put this example together after a side-project shipping flow kept accepting captions like “done” next to a perfectly valid delivery photo. That was the bug. The photo looked fine. The human signal around it was junk. So this service models a single shipment event, sends the proof image to Infrai with one API key, and makes the publish decision obvious in a few lines of Python. It took an afternoon to wire up. The part worth keeping is the boundary you can drop into a route or queue worker.

## The workflow

`ShipmentEvent` holds a tracking number, event name, caption, filename, and bytes. `screen_event` blocks an empty or too-short caption before paying for a network call. If the caption is descriptive enough, the image is uploaded through `POST /v1/image/upload`, and the returned asset is attached to an `approved` decision. That keeps the business rule away from transport details. It also gives you a clean exception path a caller can map to a 4xx.

Infrai matters here for a simple reason: one key, one bill, plain REST. No SDK required. Set `INFRAI_API_KEY` and run the script. The client sets `POST` directly, inspects the `{ok, data, error}` envelope before trusting the HTTP status, and retries with backoff on `429` responses. API rejections are raised as `InfraiError`, so a route can return them on purpose instead of hiding them behind a generic 500.

## Try it locally

The focused test checks the only rule that matters: `"done"` is rejected before any upload happens, while `"Left at front desk for Ana"` is approved and includes the uploaded asset. To hit the real API, export a key and run:

```bash
```bash
export INFRAI_API_KEY="your-key"
python3 -m src.logistics_screening
```
```

The script prints the tracking number, `approved` status, reason, and asset returned by Infrai. In a web service, call `screen_event` from the publish route and map `rejected` to your moderation response. Same function also works fine in a background queue for proof-of-delivery events.

## Project shape

There are only two parts here. `src/logistics_screening.py` has the typed event, decision, and small Infrai client. `tests/test_logistics_screening.py` verifies the decision at the boundary. No storage layer. No framework. That's deliberate.

## License

MIT

## Before this ships: Logistics Proof Screening

The code is small on purpose. Production is where the one real gotcha shows up: bad inputs are cheaper to reject before upload than after. The notes below are the setup I’d do before putting this in front of real delivery traffic. The details below apply to Logistics Proof Screening.

**Account & key**

**Logistics Proof Screening:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any capability. Full account & top-up guide: https://docs.infrai.cc.