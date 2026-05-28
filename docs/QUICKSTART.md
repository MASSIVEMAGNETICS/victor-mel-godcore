# Quickstart — victor-mel-godcore

## Installation

```bash
git clone https://github.com/MASSIVEMAGNETICS/victor-mel-godcore.git
cd victor-mel-godcore
pip install -e .
```

## Run the Demo (Recommended First Step)

```bash
python run_demo.py
# or
python -m examples.educational_mel_demo
```

You will see:
- A maglev flywheel spin up
- Resonant wireless power delivery with metamaterial boost
- A clean energy ledger with **zero violations**
- A "MEL Elegance Score" that shows how magical the system feels while remaining 100% honest

## Core Usage Example

```python
from victor_mel.mel import MELController
from victor_mel.primitives import EnergyAuditor

auditor = EnergyAuditor(name="my_mel", tolerance_joules=1.0)
mel = MELController(auditor=auditor)

# Pre-charge the flywheel
mel.flywheel.charge(350, 15)

# Deliver 120W wirelessly for 30 seconds
result = mel.maintain_power(load_w=120, duration_s=30)

print(result["final_status"])
print("Energy violations:", auditor.get_snapshot().apparent_violation)
```

## Key Guarantee

If `auditor.get_snapshot().apparent_violation` is ever True after normal operation, something is wrong with either the physics model or the implementation. This is treated as a critical fault.

## Next Steps

- Read `README.md` for the full philosophy
- Explore `src/victor_mel/mel/` for the digital twin
- Look at the 10 algorithms (coming in next iterations)
- Study `tests/test_energy_balance.py` for the enforcement layer
