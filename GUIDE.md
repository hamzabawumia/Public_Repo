# Supermed Ultra: Maternity / ANC + Insurance Claims
## Installation guide (manual, step by step)

This guide adds the two features to your dev instance **without replacing your codebase**.
Your uploaded `Supermed-Ultra-main` is the baseline. Every line number below refers to **your original files**
("Original file: lines …") and to the updated copies in `2_EDITED_FILES_full_updated_copies/` ("Updated file: lines …").

What's in this folder:

| Folder | What it is | What you do with it |
|---|---|---|
| `1_NEW_FILES_copy_as_is/` | Files that **don't exist** in your app yet (5 new doctypes, 2 Python modules, 2 JS files, 2 pages, 2 print formats, 1 workspace, 1 doc) | Copy into your app at the same path |
| `2_EDITED_FILES_full_updated_copies/` | Full updated copies of the **4 existing code files** I changed | **Don't overwrite yours.** Apply the edits in **Section 7** by hand, then compare with these if you like |
| `3_REFERENCE_ONLY_doctype_json_do_not_copy/` | What your existing doctype JSONs should contain **after** you finish the desk-UI edits in Section 3 | Compare only. Don't copy |

---

## 0. Change audit: what changed in your existing files

I compared your original upload with the updated code function by function (Python parsed with `ast`,
JavaScript parsed with `acorn`), and line by line with a diff.

**Result: no function, class, field or permission of yours was removed. All 102 JS functions and handlers and all 42 Python functions and assignments in the edited files still exist.**

### 0.1 Code files

| File | Added | Modified (in place) | Removed |
|---|---|---|---|
| `hooks.py` | `jinja = {...}` (replaces the commented-out example) | `doctype_js["patient_encounter"]`: +2 JS files · `LIST_OF_CUSTOM_FIELD_DOCTYPES`: +`"Item"` | none |
| `doctype/patient_encounter/patient_encounter.py` | `on_update()`, `_set_insurance_claim_total()` | `validate()`: +1 call · `before_save()`: +1 call · `_validate_24_hour_edit_lock()`: exempt set extended | none |
| `doctype/patient_encounter/patient_encounter.js` | `ROLE_FORM_RULES["midwife_smu"]`, `resolve_role_rule()`, `get_base_form_rule()` | `ROLE_FORM_RULES` receptionist / doctor / superuser: +2 fields in `allowed_fields` · `get_requested_layout_role()`: +`midwife` in map · `get_active_form_rule()`: now a wrapper (its original body is `get_base_form_rule()`, see 0.3) · `apply_parent_time_lock()`: +1 guard · `refresh` handler: +1 filter, +1 call | none |
| `doctype/pregnancy_episode/pregnancy_episode.py` | `validate()`, `_validate_single_active_episode()` | none (class kept) | only the placeholder `pass` and the commented `# import frappe` |

### 0.2 Doctypes (you'll make these changes in the desk UI, Section 3)

| Doctype | Fields added | Fields changed | Fields removed |
|---|---|---|---|
| `patient_encounter` | 20 | 1: `anc_attendance_type` (label + options, moved up next to *Encounter Type*) | none |
| `Pregnancy Episode` | 8 | 1: `estimated_due_date` no longer mandatory | none (+7 permission rows) |
| `Out_patient_code`, `In_patient_code`, `Investigation_code`, `Pharmacy_code`, `Procedure_code` | 2 each | none | none |
| `Baby Form` | none | none | none (used as-is as the baby table) |

### 0.3 Behaviour your existing workflows keep

- **Encounter form layouts are unchanged for every existing role.** I loaded your original `patient_encounter.js` and the
  updated one side by side and compared them on **120 combinations**: 12 role sets (receptionist, doctor, nurse, superuser,
  cashier, pharmacist, laboratory, admin, insurance, System Manager, doctor+nurse, cashier+doctor) × new / existing / admitted /
  past-24h-locked / walk-in encounters × with and without `?layout=cashier`.
  Tabs, tab order, default tab, visible fields, hidden fields and read-only flags were **identical in all 120**.
  The only differences are the two new fields (*ANC / Maternity Attendance*, *Pregnancy*), which are intentionally visible
  to receptionist, doctor and superuser.
- **The role-rule refactor in `get_active_form_rule()`:** the original body moved unchanged into `get_base_form_rule()`.
  The only change is that each rule is returned as a copy tagged with `__role`, so the maternity code knows which role's layout is in use.
  On ANC encounters a user who also holds `midwife_smu` gets the midwife layout first. Nothing changes anywhere else.
- **Server side, non-maternity encounters:** `sync_encounter_maternity()` returns immediately unless *ANC / Maternity Attendance* is set.
- **`insurance_claim_summary_total`:** left exactly as today. Auto-calculation is **off** unless you tick it in *Insurance Claim Settings*.
- **24-hour lock:** unchanged, except on encounters marked *For Labour & Delivery*, where the labour and delivery fields stay editable.

### 0.4 Tests run

| Check | Result |
|---|---|
| All doctype JSON valid; Link/Table targets exist; every `.py` compiles; every `.js` parses | pass (one problem predates this work: `Insurance Item Price.item` → `items_list` doesn't exist) |
| Claim maths: NHIS all-inclusive, NHIS unbundled (admitted / not admitted), corporate with co-pay | pass |
| Claim-it XML vs your Django `export_claim_it_xml/1_working_examples/single_claim` | same 51 elements, same order, same values (`physicianID` is a setting) |
| Maternity: booking → review → labour → delivery, gestational age, EDD, partograph < 4 cm rejected, unbooked labour, risk factors | pass |
| Encounter form as midwife / nurse / doctor / pharmacist / cashier / System Manager on ANC encounters | 21/21 pass |
| Original vs new form behaviour, 120 combinations | 0 differences |
| Print formats rendered (sandboxed Jinja, like Frappe) | pass |

These tests used a stand-in for Frappe, **not a live bench**, so do the smoke test in Section 10 on your dev site.

---

## 1. Before you start

1. Work on your **dev** site with developer mode on (`bench --site <site> set-config developer_mode 1`), so DocType edits
   in the desk are written back to the JSON files in your app.
2. Commit or back up your app folder, and back up the site:
   `bench --site <site> backup`
3. Order matters: the new child doctypes must exist **before** you add Table fields that point to them.

| Step | Where | Section |
|---|---|---|
| 1 | Copy the 5 new doctypes → `bench migrate` | 2 |
| 2 | Desk UI: role, then the existing doctypes | 3 |
| 3 | Desk UI: Item custom fields (Customize Form) | 4 |
| 4 | Desk UI: Role Permission Manager | 5 |
| 5 | Copy the remaining new files (Python, JS, pages, print formats, workspace) | 6 |
| 6 | Hand-edit 4 existing files | 7 |
| 7 | Migrate, build, export fixtures | 8 |
| 8 | Fill master data (tariffs, NHIS codes, settings) | 9 |
| 9 | Smoke test | 10 |

---

## 2. Copy the new doctypes, then migrate

Copy these five folders from `1_NEW_FILES_copy_as_is/` to the same place in your app
(`apps/supermed_ultra/supermed_ultra/supermed_ultra/doctype/`):

| Folder | DocType | Kind | Used for |
|---|---|---|---|
| `anc_past_pregnancy/` | ANC Past Pregnancy | Child table | Past pregnancies at ANC booking |
| `partograph_entry/` | Partograph Entry | Child table | Partograph plots (cervix, descent, contractions…) |
| `foetal_heart_rate_entry/` | Foetal Heart Rate Entry | Child table | FHR readings in labour |
| `labour_vital_signs/` | Labour Vital Signs | Child table | Maternal vitals in labour |
| `insurance_claim_settings/` | Insurance Claim Settings | Single | Facility name, HI code, Claim-it options |

```bash
bench --site <site> migrate
```

Check that `/app/doctype/ANC Past Pregnancy` (and the other four) open.

---

## 3. Desk UI: role and existing doctypes

### 3.1 Create the Midwife role

**/app/role/new**

| Field | Value |
|---|---|
| Role Name | `midwife_smu` |
| Desk Access | ✔ |
| Home Page | `/app/maternity-(supermed)` (optional; this workspace is added in Section 6) |

Assign it to your midwives (User → Roles).

### 3.2 `patient_encounter`: 1 change + 20 new fields

Open **/app/doctype/patient_encounter** (the DocType editor, **not** Customize Form, so the change lands in your app's JSON).
For each row, add the field and place it **directly after** the field in the last column.
Leave every property not listed at its default.

**A. Change an existing field**

| Field | Change |
|---|---|
| `anc_attendance_type` (currently the first field in *Antenatal Consulting Section*) | **Label:** `ANC / Maternity Attendance` · **Options** (one per line; keep the first line blank): <br>`(blank line)`<br>`For Booking (Now Starting)`<br>`For Review`<br>`For Labour & Delivery`<br>**Move it** to sit directly after **`encounter_type`** (top of the form). |

> Why the move is required: the *Antenatal Consulting Section* is hidden on normal encounters and moved into the maternity
> tabs on ANC encounters. Reception has to see this field to mark an encounter as ANC, so it can't stay inside that section.
> The option text must match exactly; the code compares these strings.

**B. New fields** (type the *Name* exactly; the code uses these fieldnames)

| # | Label | Type | Name | Options | Other properties | Place directly after |
|---|---|---|---|---|---|---|
| 1 | Pregnancy (ANC Booking) | Link | `pregnancy_episode` | `Pregnancy Episode` | Depends On: `eval:doc.anc_attendance_type` | `anc_attendance_type` |
| 2 | Card Serial No. | Data | `card_serial_no` | | | `insurance_number` |
| 3 | Is Dependant | Check | `is_dependant` | | | `card_serial_no` |
| 4 | Maternity Summary | Section Break | `maternity_summary_section` | | | `procedure_code` (i.e. just before *Antenatal Consulting Section*) |
| 5 | Maternity Summary | HTML | `maternity_summary` | | | `maternity_summary_section` |
| 6 | LMP (Last Menstrual Period) | Date | `lmp` | | | `no_of_induced_abortions` |
| 7 | EDD by LMP | Date | `edd_by_lmp` | | Read Only ✔ | `lmp` |
| 8 | Past Obstetric History | Small Text | `past_obstetric_history` | | | `obstetric_examination` |
| 9 | Pelvic Examination | Small Text | `pelvic_examination` | | | `past_obstetric_history` |
| 10 | Past Pregnancies | Section Break | `past_pregnancies_section` | | | `hb_electrophoresis` (i.e. just before *anc_progress_section*) |
| 11 | Past Pregnancies | Table | `past_pregnancies` | `ANC Past Pregnancy` | | `past_pregnancies_section` |
| 12 | Partograph | Section Break | `labour_monitoring_section` | | | `caput` (last field of *LABOUR FORM*) |
| 13 | Partograph Chart | HTML | `partograph_chart` | | | `labour_monitoring_section` |
| 14 | Partograph | Table | `partograph` | `Partograph Entry` | | `partograph_chart` |
| 15 | Foetal Heart Rate Monitoring | Section Break | `foetal_heart_rate_section` | | | `partograph` |
| 16 | Foetal Heart Rate | Table | `foetal_heart_rate_entries` | `Foetal Heart Rate Entry` | | `foetal_heart_rate_section` |
| 17 | Maternal Vital Signs During Labour | Section Break | `labour_vitals_section` | | | `foetal_heart_rate_entries` |
| 18 | Labour Vital Signs | Table | `labour_vitals` | `Labour Vital Signs` | | `labour_vitals_section` |
| 19 | Baby Details | Section Break | `babies_section` | | | `delivery_supervised_by` (last field of the form) |
| 20 | Babies | Table | `babies` | `Baby Form` | | `babies_section` |

> Positions matter. The maternity tabs are built from the sections, and a field belongs to the section above it.
> #10–11 must come after `hb_electrophoresis` and **before** `anc_progress_section`.
> #12–18 must come after `caput` and **before** the unlabelled delivery section (`section_break_qdhy`).

Click **Save**. Then compare with `3_REFERENCE_ONLY_doctype_json_do_not_copy/patient_encounter.json`: every fieldname in its `field_order`
should be in yours, in the same order.

### 3.3 `Pregnancy Episode`: 8 new fields, 1 change, permissions

Open **/app/doctype/Pregnancy Episode**

**Change:** `estimated_due_date`: **untick Mandatory**. The episode is opened when reception books the visit, before the midwife has the LMP.
The EDD is then calculated from the LMP.

**New fields**

| # | Label | Type | Name | Options | Other properties | Place directly after |
|---|---|---|---|---|---|---|
| 1 | Patient Name | Data | `patient_name` | | Fetch From: `patient.patient_name` · Read Only ✔ | `patient` |
| 2 | Unbooked (first seen in labour) | Check | `unbooked` | | Read Only ✔ | `gestational_age_at_booking` (last field) |
| 3 | Booking Encounter | Link | `booking_encounter` | `patient_encounter` | Read Only ✔ | `unbooked` |
| 4 | Delivery | Section Break | `delivery_section` | | | `booking_encounter` |
| 5 | Delivery Date | Date | `delivery_date` | | Read Only ✔ | `delivery_section` |
| 6 | Delivery Encounter | Link | `delivery_encounter` | `patient_encounter` | Read Only ✔ | `delivery_date` |
| 7 | Mode of Delivery | Data | `mode_of_delivery` | | Read Only ✔ | `delivery_encounter` |
| 8 | Number of Babies | Int | `number_of_babies` | | Read Only ✔ | `mode_of_delivery` |

**Permissions** (Permission Rules table at the bottom of the DocType; keep your System Manager row):

| Role | Read | Write | Create | Print | Report |
|---|---|---|---|---|---|
| midwife_smu | ✔ | ✔ | ✔ | ✔ | ✔ |
| doctor_smu | ✔ | ✔ | ✔ | ✔ | ✔ |
| superuser_smu | ✔ | ✔ | ✔ | ✔ | ✔ |
| admin_smu | ✔ | ✔ | ✔ | ✔ | ✔ |
| nurse_smu | ✔ | | | ✔ | ✔ |
| insurance_smu | ✔ | | | ✔ | ✔ |
| receptionist_smu | ✔ | | | ✔ | ✔ |

Save. Reference: `3_REFERENCE_ONLY…/pregnancy_episode.json`.

### 3.4 The five G-DRG / code doctypes: 2 new fields each

Do this on **each** of: **Out_patient_code**, **In_patient_code**, **Investigation_code**, **Pharmacy_code**, **Procedure_code**.
Add both fields at the end of the field list.

| Label | Type | Name |
|---|---|---|
| Description | Data | `description` |
| Tariff Amount | Currency | `tariff_amount` |

The claim maths uses `tariff_amount` for the out-patient and in-patient G-DRG tariffs on the NHIS form and in the Claim-it totals.

---

## 4. Desk UI: two custom fields on Item (Customize Form)

**/app/customize-form** → Enter Form Type: **Item** → add the two rows below *Item Group* → **Update**.

| Label | Type | Name (Frappe adds the `custom_` prefix) | Description |
|---|---|---|---|
| NHIS Code | Data | `custom_nhis_code` | NHIS medicine code (e.g. PARACETA1) or procedure G-DRG (e.g. OBGY34A) |
| NHIS ICD-10 (procedures) | Data | `custom_nhis_icd10` | ICD-10 sent with procedures in the Claim-it XML |

If you type `nhis_code` as the fieldname, Frappe saves it as `custom_nhis_code`. Make sure the final names are exactly those two.

---

## 5. Desk UI: Role Permission Manager

**/app/permission-manager**

### 5.1 `midwife_smu`: same access as `doctor_smu`

Add a `midwife_smu` row (level 0) on each document type below, ticking exactly these boxes. They mirror your current `doctor_smu` rows:

| Document Type | Ticks |
|---|---|
| patient_encounter | Read, Write, Print, Report, Select |
| Patient | Read |
| Diagnosis | Read, Write, Create, Select |
| Diagnosis List | Read, Write, Create, Export |
| List of Complaints | Read, Write, Create, Report |
| Item | Read, Report |
| Lab Test | Read, Report |
| Lab Test Template | Read, Report |
| Medication | Read, Select |
| Customer | Read, Create, Export |

### 5.2 `insurance_smu` on `patient_encounter`

Your fixtures have **no** `insurance_smu` row on `patient_encounter`, so insurance officers currently can't open encounters
(only the 24-hour-lock bypass refers to them). Add:

| Document Type | Role | Ticks |
|---|---|---|
| patient_encounter | insurance_smu | Read, Write, Print, Report, Export, Select |

### 5.3 Optional: let insurance officers maintain tariffs

The five code doctypes currently allow **System Manager** only. If insurance officers should enter tariffs, add
`insurance_smu` with Read, Write, Create, Report, Export on each of them (in the DocType's Permission Rules, like 3.3).
Not needed if a System Manager enters the tariffs.

---

## 6. Copy the remaining new files

From `1_NEW_FILES_copy_as_is/` copy into your app (`apps/supermed_ultra/`), keeping the same paths:

| Path | What it is |
|---|---|
| `supermed_ultra/maternity.py` | Maternity server logic: episode linking, EDD and gestational age, partograph validation, delivery outcome, Maternity Summary and Maternity Desk APIs |
| `supermed_ultra/insurance_claims.py` | Claim engine (`build_claim`), NHIS and corporate totals, claim checks, Claim-it XML, Insurance Claims APIs, Jinja helpers for the print formats |
| `supermed_ultra/public/js/maternity_encounter.js` | Maternity tabs, Maternity Summary panel, partograph chart, LMP → EDD |
| `supermed_ultra/public/js/insurance_encounter.js` | "Insurance Claim" buttons and the claim-check banner on the encounter |
| `supermed_ultra/supermed_ultra/page/maternity_desk/` | **Maternity Desk** page |
| `supermed_ultra/supermed_ultra/page/insurance_claims/` | **Insurance Claims** page |
| `supermed_ultra/supermed_ultra/print_format/nhis_claim_form/` | **NHIS Claim Form** print format (standard, Jinja) |
| `supermed_ultra/supermed_ultra/print_format/corporate_insurance_claim/` | **Corporate Insurance Claim** print format |
| `supermed_ultra/supermed_ultra/workspace/maternity_(supermed)/` | **Maternity (Supermed)** workspace (optional; you can build it in the UI instead, see 8.3) |
| `supermed_ultra/OVERALL_Project_Design_Documentation/1. Main Use Cases & Features/12. Maternity (ANC) and Insurance Claims.md` | Feature documentation (optional) |

Every folder includes its `__init__.py`. Copy those too.

---

## 7. Hand-edit 4 existing files

Each edit shows your **original** lines (to find) and the **updated** lines (to paste), with 3 lines of unchanged context above and below.
Do the edits **top to bottom**: line numbers in "Original file" are your file before any edit.
The full updated file is in `2_EDITED_FILES_full_updated_copies/` if you want to check your result.

### 7.1 `supermed_ultra/hooks.py`

*393 -> 399 lines, 3 edits*

3 edits: register the two new JS files on `patient_encounter`, enable the Jinja helpers used by the claim print formats, and add `Item` to the custom-field fixture list so the two NHIS fields get exported.

> Edit 1 shows `"public/js/patient_encounter.js"` as removed: the line is kept and only gains a trailing comma.
> Edit 3: adding `Item` means `bench export-fixtures` will now also export **every** Custom Field and Property Setter on Item into this app's fixtures. That's the same behaviour as your other entries in the list; check the export before committing (Section 8).

#### Edit 1 of 3 — REPLACE

**Original file: lines 62–68**  →  **Updated file: lines 62–70**

Before (your original, find this):

```python
doctype_js = {
    "patient_encounter": [
        "public/js/unified_bill_renderer.js",
        "public/js/patient_encounter.js"
    ],

    "lab_test": ["public/js/lab_test.js"]
```

After (replace it with this):

```python
doctype_js = {
    "patient_encounter": [
        "public/js/unified_bill_renderer.js",
        "public/js/patient_encounter.js",
        "public/js/maternity_encounter.js",   # ANC / labour tabs, summary, partograph
        "public/js/insurance_encounter.js",   # claim form print + Claim-it XML buttons
    ],

    "lab_test": ["public/js/lab_test.js"]
```

#### Edit 2 of 3 — REPLACE

**Original file: lines 98–107**  →  **Updated file: lines 100–112**

Before (your original, find this):

```python
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "supermed_ultra.utils.jinja_methods",
# 	"filters": "supermed_ultra.utils.jinja_filters"
# }

# Installation
# ------------
```

After (replace it with this):

```python
# ----------

# add methods and filters to jinja environment
# Used by the "NHIS Claim Form" and "Corporate Insurance Claim" print formats
jinja = {
    "methods": [
        "supermed_ultra.insurance_claims.get_insurance_claim",
        "supermed_ultra.insurance_claims.claim_money",
    ],
}

# Installation
# ------------
```

#### Edit 3 of 3 — INSERT (nothing removed)

**Original file: lines 314–319**  →  **Updated file: lines 319–325**

Before (your original, find this):

```python
    "Lab Prescription",
    "Lab Test",
    "Lab Test Template",
    # add any other erpnext / core / healthcare doctypes you customize here
]

```

After (replace it with this):

```python
    "Lab Prescription",
    "Lab Test",
    "Lab Test Template",
    "Item",                 # custom_nhis_code / custom_nhis_icd10 for NHIS claims
    # add any other erpnext / core / healthcare doctypes you customize here
]

```


---

### 7.2 `supermed_ultra/supermed_ultra/doctype/patient_encounter/patient_encounter.py`

*729 -> 762 lines, 4 edits*

4 edits, all additive:

- **Edit 1:** `before_save()` gets one call to `_set_insurance_claim_total()`, and two **new** methods, `on_update()` and `_set_insurance_claim_total()`, are added right after it. The claim total is **off** unless enabled in *Insurance Claim Settings*.
- **Edit 2:** `validate()` gets one call to `sync_encounter_maternity(self)`. It returns immediately for non-ANC encounters.
- **Edits 3 and 4:** `_validate_24_hour_edit_lock()` imports `lock_exempt_fields`, and the exempt set gains `| lock_exempt_fields(self)`. That's empty unless the encounter is *For Labour & Delivery*.

No existing line is deleted. The single `-            },` in the diff is the closing of the exempt set, re-added as `} | lock_exempt_fields(self),`.

#### Edit 1 of 4 — INSERT (nothing removed)

**Original file: lines 116–122**  →  **Updated file: lines 116–148**

Before (your original, find this):

```python
    def before_save(self):
        self.apply_consultation_pricing()
        self.reorder_miscellaneous_rows()
        self._validate_24_hour_edit_lock()

    def validate(self):
        """
```

After (replace it with this):

```python
    def before_save(self):
        self.apply_consultation_pricing()
        self.reorder_miscellaneous_rows()
        self._set_insurance_claim_total()
        self._validate_24_hour_edit_lock()

    def on_update(self):
        # Maternity: link the Pregnancy Episode back to this encounter
        # (booking / delivery) now that the encounter exists in the DB.
        from supermed_ultra.maternity import after_encounter_save
        after_encounter_save(self)

    def _set_insurance_claim_total(self):
        """
        Optional (Insurance Claim Settings > Auto-calculate ...): keep
        insurance_claim_summary_total in step with the claim the insurance
        officer will print / export. Off by default. Never blocks a save.
        """
        if (self.payer_type or "Cash") == "Cash" or self.is_walkin_request():
            return
        try:
            from supermed_ultra.insurance_claims import build_claim, get_settings
            if not frappe.utils.cint(get_settings().auto_update_claim_summary_total):
                return  # default: leave the field exactly as before
            self.insurance_claim_summary_total = build_claim(self)["totals"]["claim_total"]
        except Exception:
            frappe.log_error(
                title=f"Insurance claim total failed for {self.name}",
                message=frappe.get_traceback(),
            )

    def validate(self):
        """
```

#### Edit 2 of 4 — INSERT (nothing removed)

**Original file: lines 149–154**  →  **Updated file: lines 175–185**

Before (your original, find this):

```python
        """
        self._validate_consultation_type_present()

        orders_map = {
            "xrays_scans": "Radiology",
            "registration_and_consultation_types": "Consultation Types",
```

After (replace it with this):

```python
        """
        self._validate_consultation_type_present()

        # Maternity / ANC: link or open the Pregnancy Episode, compute EDD and
        # gestational age, validate the partograph.
        from supermed_ultra.maternity import sync_encounter_maternity
        sync_encounter_maternity(self)

        orders_map = {
            "xrays_scans": "Radiology",
            "registration_and_consultation_types": "Consultation Types",
```

#### Edit 3 of 4 — INSERT (nothing removed)

**Original file: lines 169–174**  →  **Updated file: lines 200–207**

Before (your original, find this):

```python


    def _validate_24_hour_edit_lock(self):
        validate_time_based_lock(
            self,
            lock_after_hours=24,
```

After (replace it with this):

```python


    def _validate_24_hour_edit_lock(self):
        from supermed_ultra.maternity import lock_exempt_fields

        validate_time_based_lock(
            self,
            lock_after_hours=24,
```

#### Edit 4 of 4 — REPLACE

**Original file: lines 179–185**  →  **Updated file: lines 212–218**

Before (your original, find this):

```python
                "insurance_utilized",
                "patient_payable",
                "insurance_claim_summary_total",
            },
        )


```

After (replace it with this):

```python
                "insurance_utilized",
                "patient_payable",
                "insurance_claim_summary_total",
            } | lock_exempt_fields(self),
        )


```


---

### 7.3 `supermed_ultra/supermed_ultra/doctype/pregnancy_episode/pregnancy_episode.py`

*9 -> 44 lines, 1 edits*

Your file is the 9-line generated stub (`class PregnancyEpisode(Document): pass`). The edit fills in the class with `validate()`: EDD from LMP, gestational age at booking, LMP not in the future, and only one *Active* pregnancy per patient.
The class name, imports and file header stay as they are; only `# import frappe` becomes real imports and `pass` is replaced.

#### Edit 1 of 1 — REPLACE

**Original file: lines 1–9**  →  **Updated file: lines 1–44**

Before (your original, find this):

```python
# Copyright (c) 2026, Hamza Bawumia and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PregnancyEpisode(Document):
	pass
```

After (replace it with this):

```python
# Copyright (c) 2026, Hamza Bawumia and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate


class PregnancyEpisode(Document):
	"""One pregnancy of one mother (Django: Obs_anc_booking / anc_booking_number).

	Every ANC visit and the labour encounter of this pregnancy link here
	through patient_encounter.pregnancy_episode.
	"""

	def validate(self):
		from supermed_ultra.maternity import PREGNANCY_DAYS, gestational_age_label

		if self.lmp and not self.estimated_due_date:
			self.estimated_due_date = add_days(getdate(self.lmp), PREGNANCY_DAYS)

		if self.lmp and self.booking_date and not self.gestational_age_at_booking:
			self.gestational_age_at_booking = gestational_age_label(self.lmp, self.booking_date)

		if self.lmp and getdate(self.lmp) > getdate():
			frappe.throw(_("LMP cannot be in the future."))

		self._validate_single_active_episode()

	def _validate_single_active_episode(self):
		if self.pregnancy_status != "Active":
			return
		other = frappe.db.get_value(
			"Pregnancy Episode",
			{"patient": self.patient, "pregnancy_status": "Active", "name": ["!=", self.name]},
			"name",
		)
		if other:
			frappe.throw(
				_("Patient {0} already has an active pregnancy record ({1}). Close or update "
				  "that one before opening another.").format(self.patient, other),
				title=_("Duplicate Active Pregnancy"),
			)
```


---

### 7.4 `supermed_ultra/supermed_ultra/doctype/patient_encounter/patient_encounter.js`

*2868 -> 2945 lines, 9 edits*

9 edits:

| Edit | Where | What |
|---|---|---|
| 1 | `ROLE_FORM_RULES.receptionist_smu` | +`"anc_attendance_type"` in `allowed_fields` |
| 2 | `ROLE_FORM_RULES.doctor_smu` | +`"anc_attendance_type"`, `"pregnancy_episode"` in `allowed_fields` |
| 3 | before `"cashier_smu"` | **new** `"midwife_smu"` rule |
| 4 | `ROLE_FORM_RULES.superuser_smu` | +`"anc_attendance_type"`, `"pregnancy_episode"` in `allowed_fields` |
| 5 | `get_requested_layout_role()` | +`midwife: "midwife_smu"` (enables `?layout=midwife`) |
| 6 | `get_active_form_rule()` | becomes a 6-line wrapper. Your **original body is kept** as `get_base_form_rule()`; the only body change is that each `return` gives a copy tagged with `__role` via the new `resolve_role_rule()`, and on ANC encounters `midwife_smu` is tried first |
| 7 | `apply_parent_time_lock()` | +1 guard: labour fields stay editable after 24h on labour encounters |
| 8 | `refresh` → child-tab builder | maternity tables are skipped by the generic tab builder (they live inside the maternity tabs) |
| 9 | `refresh` → child-tab builder | +1 call to `window.supermed_maternity.build_tabs(...)`. On normal encounters it only hides the maternity sections |

Every call into the new code is guarded (`window.supermed_maternity?.…`), so if `maternity_encounter.js` isn't loaded the form behaves exactly as before.

#### Edit 1 of 9 — INSERT (nothing removed)

**Original file: lines 77–82**  →  **Updated file: lines 77–83**

Before (your original, find this):

```javascript
                "payer_type",
                "insurance_company",
                "insurance_package",
            ],

            readonly_fields: [
```

After (replace it with this):

```javascript
                "payer_type",
                "insurance_company",
                "insurance_package",
                "anc_attendance_type",   // maternity: booking / review / labour
            ],

            readonly_fields: [
```

#### Edit 2 of 9 — INSERT (nothing removed)

**Original file: lines 121–126**  →  **Updated file: lines 122–129**

Before (your original, find this):

```javascript
                "full_history",
                "admitted",
                "drug_administration",
                // "miscellaneous_panel",
            ],

```

After (replace it with this):

```javascript
                "full_history",
                "admitted",
                "drug_administration",
                "anc_attendance_type",
                "pregnancy_episode",
                // "miscellaneous_panel",
            ],

```

#### Edit 3 of 9 — INSERT (nothing removed)

**Original file: lines 295–300**  →  **Updated file: lines 298–353**

Before (your original, find this):

```javascript
    },


    "cashier_smu": function(frm) {
        return {
            allowed_tables: [],   // no child tables at all
```

After (replace it with this):

```javascript
    },


    // Midwives run ANC clinics and the labour ward. Their maternity tabs
    // (ANC Booking / ANC Visit / Labour & Partograph / Delivery & Baby) are
    // added by window.supermed_maternity.extend_rule() for ANC encounters.
    "midwife_smu": function(frm) {
        const base = {
            allowed_tables: [
                "vitals_signs",
                "nurses_notes",
                "diagnosis",
                "prescriptions",
                "lab_tests",
                "procedures",
                "xrays_scans",
            ],
            allowed_fields: [
                "patient_id",
                "payer_type",
                "anc_attendance_type",
                "pregnancy_episode",
                "height",
                "weight",
                "bmi",
                "age",
                "insurance_company",
                "insurance_package",
                "assigned_to",
                "list_of_complaints",
                "full_history",
                "admitted",
                "detain_patient",
                "drug_administration",
                "miscellaneous_panel",
            ],
            readonly_fields: [
                "patient_id",
                "payer_type",
                "insurance_company",
                "insurance_package",
                "assigned_to",
            ],
            default_tab: "vitals_signs"
        };

        if (frm.doc.admitted || frm.doc.detain_patient) {
            base.allowed_tables.push("doctors_reviews", "case_summary");
        }
        return base;
    },


    "cashier_smu": function(frm) {
        return {
            allowed_tables: [],   // no child tables at all
```

#### Edit 4 of 9 — INSERT (nothing removed)

**Original file: lines 341–346**  →  **Updated file: lines 394–401**

Before (your original, find this):

```javascript
                "list_of_complaints",
                "full_history",
                "admitted",
            ],


```

After (replace it with this):

```javascript
                "list_of_complaints",
                "full_history",
                "admitted",
                "anc_attendance_type",
                "pregnancy_episode",
            ],


```

#### Edit 5 of 9 — INSERT (nothing removed)

**Original file: lines 417–422**  →  **Updated file: lines 472–478**

Before (your original, find this):

```javascript
        cashier: "cashier_smu",
        doctor: "doctor_smu",
        nurse: "nurse_smu",
        receptionist: "receptionist_smu",
        pharmacist: "pharmacist_smu",
        laboratory: "laboratory_smu",
```

After (replace it with this):

```javascript
        cashier: "cashier_smu",
        doctor: "doctor_smu",
        nurse: "nurse_smu",
        midwife: "midwife_smu",
        receptionist: "receptionist_smu",
        pharmacist: "pharmacist_smu",
        laboratory: "laboratory_smu",
```

#### Edit 6 of 9 — REPLACE

**Original file: lines 518–568**  →  **Updated file: lines 574–632**

Before (your original, find this):

```javascript


function get_active_form_rule(frm) {
    const roles = frappe.user_roles || [];
    const requested_role = get_requested_layout_role();

    // Walk-in Request layout takes precedence over every other rule.
    if (is_walkin_request(frm)) {
        const walkin_rule = get_walkin_form_rule(frm);
        if (walkin_rule) return walkin_rule;
    }

    // 0) New Patient Encounter: force receptionist layout (if user has role)
    // Handles routes like /app/patient_encounter/new-patient_encounter-xxxx
    if (frm && frm.is_new && frm.is_new() && roles.includes("receptionist_smu")) {
        const receptionist_rule = ROLE_FORM_RULES["receptionist_smu"];
        if (receptionist_rule) {
            return typeof receptionist_rule === "function"
                ? receptionist_rule(frm)
                : receptionist_rule;
        }
    }

    // 1) Explicit URL layout context (e.g. ?layout=cashier) still wins after new-doc rule
    if (requested_role && roles.includes(requested_role)) {
        const requested_rule = ROLE_FORM_RULES[requested_role];
        if (requested_rule) {
            return typeof requested_rule === "function"
                ? requested_rule(frm)
                : requested_rule;
        }
    }

    // 2) Default fallback for existing documents:
    // non-cashier roles first, cashier last
    const ordered_roles = [
        ...roles.filter(role => role !== "cashier_smu"),
        ...roles.filter(role => role === "cashier_smu")
    ];

    for (const role of ordered_roles) {
        const rule = ROLE_FORM_RULES[role];
        if (rule) {
            return typeof rule === "function" ? rule(frm) : rule;
        }
    }

    return ROLE_FORM_RULES["_default"];
}

// Adding the 24hr locking logic for encounters
```

After (replace it with this):

```javascript


function get_active_form_rule(frm) {
    const rule = get_base_form_rule(frm);
    // Maternity / ANC encounters: open the maternity tabs for midwives,
    // doctors (and labour monitoring for nurses). See maternity_encounter.js.
    return window.supermed_maternity
        ? window.supermed_maternity.extend_rule(frm, rule)
        : rule;
}

function resolve_role_rule(role, frm) {
    const rule = ROLE_FORM_RULES[role];
    if (!rule) return null;
    const resolved = typeof rule === "function" ? rule(frm) : rule;
    return Object.assign({}, resolved, { __role: role });
}

function get_base_form_rule(frm) {
    const roles = frappe.user_roles || [];
    const requested_role = get_requested_layout_role();

    // Walk-in Request layout takes precedence over every other rule.
    if (is_walkin_request(frm)) {
        const walkin_rule = get_walkin_form_rule(frm);
        if (walkin_rule) return Object.assign({}, walkin_rule, { __role: "walkin" });
    }

    // 0) New Patient Encounter: force receptionist layout (if user has role)
    // Handles routes like /app/patient_encounter/new-patient_encounter-xxxx
    if (frm && frm.is_new && frm.is_new() && roles.includes("receptionist_smu")) {
        const receptionist_rule = resolve_role_rule("receptionist_smu", frm);
        if (receptionist_rule) return receptionist_rule;
    }

    // 1) Explicit URL layout context (e.g. ?layout=cashier) still wins after new-doc rule
    if (requested_role && roles.includes(requested_role)) {
        const requested_rule = resolve_role_rule(requested_role, frm);
        if (requested_rule) return requested_rule;
    }

    // 2) Default fallback for existing documents:
    // midwife first on ANC encounters, non-cashier roles next, cashier last
    const is_anc = !!(window.supermed_maternity && window.supermed_maternity.is_maternity(frm));
    const ordered_roles = [
        ...(is_anc ? roles.filter(role => role === "midwife_smu") : []),
        ...roles.filter(role => role !== "cashier_smu" && !(is_anc && role === "midwife_smu")),
        ...roles.filter(role => role === "cashier_smu")
    ];

    for (const role of ordered_roles) {
        const rule = resolve_role_rule(role, frm);
        if (rule) return rule;
    }

    return Object.assign({}, ROLE_FORM_RULES["_default"], { __role: "_default" });
}

// Adding the 24hr locking logic for encounters
```

#### Edit 7 of 9 — INSERT (nothing removed)

**Original file: lines 599–604**  →  **Updated file: lines 663–672**

Before (your original, find this):

```javascript

        // Table fields must remain available so Add Row works indefinitely.
        if (field.df.fieldtype === "Table") return;

        frm.set_df_property(field.df.fieldname, "read_only", locked ? 1 : 0);
    });
```

After (replace it with this):

```javascript

        // Table fields must remain available so Add Row works indefinitely.
        if (field.df.fieldtype === "Table") return;

        // Labour & delivery fields stay editable on labour encounters
        // (labour can outlast the 24h window). Mirrors the server exemption.
        if (window.supermed_maternity?.is_time_lock_exempt(frm, field.df.fieldname)) return;

        frm.set_df_property(field.df.fieldname, "read_only", locked ? 1 : 0);
    });
```

#### Edit 8 of 9 — REPLACE

**Original file: lines 1039–1046**  →  **Updated file: lines 1107–1117**

Before (your original, find this):

```javascript
        if (!frm.__child_tabs_initialized) {
            frm.__child_tabs_initialized = true;

            const childFields = Object.values(frm.fields_dict)
            .filter(f => f.df && f.df.fieldtype === 'Table');

            if (!childFields.length) return;

```

After (replace it with this):

```javascript
        if (!frm.__child_tabs_initialized) {
            frm.__child_tabs_initialized = true;

            // Maternity tables live inside their maternity sections/tabs
            // (built by window.supermed_maternity.build_tabs below).
            const childFields = Object.values(frm.fields_dict)
            .filter(f => f.df && f.df.fieldtype === 'Table')
            .filter(f => !window.supermed_maternity?.is_maternity_table(f.df.fieldname));

            if (!childFields.length) return;

```

#### Edit 9 of 9 — INSERT (nothing removed)

**Original file: lines 1079–1084**  →  **Updated file: lines 1150–1161**

Before (your original, find this):

```javascript
                $pane.append(field.$wrapper);
                $content.append($pane);
            });

            $nav.on('click', '.nav-link', function (e) {
                e.preventDefault();
```

After (replace it with this):

```javascript
                $pane.append(field.$wrapper);
                $content.append($pane);
            });

            // Maternity / ANC tabs (no-op for non-maternity encounters,
            // which just get the maternity sections hidden).
            if (window.supermed_maternity) {
                window.supermed_maternity.build_tabs(frm, $nav, $content);
            }

            $nav.on('click', '.nav-link', function (e) {
                e.preventDefault();
```


---

## 8. Migrate, build, workspaces and **export fixtures**

```bash
bench --site <site> migrate          # new doctypes / pages / print formats / workspace folder
bench build --app supermed_ultra     # picks up public/js/maternity_encounter.js & insurance_encounter.js
bench --site <site> clear-cache
```

### 8.1 ⚠ Export fixtures, or the next migrate undoes your desk work

`hooks.fixtures` re-imports **Role**, **Custom DocPerm**, **Custom Field**, **Property Setter** and **Workspace** from
`supermed_ultra/fixtures/*.json` on **every** `bench migrate`, and it runs **after** the doctype sync.
Anything you created in Sections 3.1, 4, 5 or 8.3 only exists in the database until you export it:

```bash
bench --site <site> export-fixtures --app supermed_ultra
git diff supermed_ultra/fixtures/      # check: new midwife_smu role, midwife/insurance Custom DocPerms,
                                       # Item-custom_nhis_code / Item-custom_nhis_icd10, workspace shortcuts
```

Because `Item` is now in `LIST_OF_CUSTOM_FIELD_DOCTYPES`, check that the export didn't pick up Item custom fields or property setters
that belong to another app. Remove those from the JSON if so.

(DocType edits from Section 3 are written straight to the doctype JSON in your app because developer mode is on. They don't need exporting.)

### 8.2 Maternity workspace

Either copy the `workspace/maternity_(supermed)/` folder (Section 6) and migrate, **or** build it in the UI:
**/app/workspace** → New → *Maternity (Supermed)*, module *Supermed Ultra*, roles `midwife_smu`, `doctor_smu`, `superuser_smu`, `admin_smu`, with shortcuts:

| Label | Type | Link to |
|---|---|---|
| Maternity Desk | Page | `maternity-desk` |
| Pregnancy Records | DocType | `Pregnancy Episode` |
| ANC Attendances | DocType | `patient_encounter` (filter: ANC / Maternity Attendance is set) |
| Enter Vitals for Consultation | Report | `Patient Encounters Today` |

### 8.3 Insurance workspace: add 4 shortcuts (desk UI)

Open **Insurance (Supermed)** → Edit → add shortcuts:

| Label | Type | Link to |
|---|---|---|
| Insurance Claims | Page | `insurance-claims` |
| Out-patient G-DRG Codes | DocType | `Out_patient_code` |
| In-patient G-DRG Codes | DocType | `In_patient_code` |
| Insurance Claim Settings | DocType | `Insurance Claim Settings` |

Save, then **export fixtures (8.1)**. This workspace lives in `fixtures/workspace.json`.

---

## 9. Master data (one-off)

| What | Where | Needed for |
|---|---|---|
| Facility name, HI code, physician ID, options | **/app/insurance-claim-settings** | Claim form header, Claim-it `physicianID` |
| *Auto-calculate Insurance Claim Summary Total* | same page, **leave unticked** to keep today's behaviour | optional |
| Tariff Amount (+ Description) on each G-DRG code | Out_patient_code / In_patient_code lists | NHIS claim totals |
| NHIS Code on each NHIS medicine Item; NHIS Code + ICD-10 on procedure Items | Item form | Claim form codes, Claim-it `<medicineCode>`, `<procedure>` |
| ICD-10 on diagnoses | Diagnosis List → `diagnosis_code` | Claim form and XML `<icd10>` |

---

## 10. Smoke test on dev

**Existing workflows (should be unchanged)**
- [ ] Receptionist books a normal Cash consultation: same tabs as before, plus the *ANC / Maternity Attendance* field (left blank).
- [ ] Doctor opens a normal encounter: same tabs and default tab as before; no maternity sections visible.
- [ ] Cashier, pharmacist and lab views unchanged; walk-in request unchanged.
- [ ] An encounter older than 24h is still locked for a doctor.
- [ ] An NHIS / corporate encounter still prices and bills as before; *Insurance Claim Summary Total* isn't overwritten.

**Maternity**
- [ ] Reception books a consultation with *For Booking (Now Starting)* → after save, *Pregnancy* shows a new Pregnancy Episode.
- [ ] Midwife opens it: tabs *Maternity Summary · ANC Booking · ANC Visit* come first, and *ANC Booking* opens.
- [ ] Enter LMP → *EDD by LMP* fills in; save → Gestational Age fills in; the Pregnancy Episode has LMP, EDD, G/P.
- [ ] A second visit *For Review* → links to the same pregnancy; *Maternity Summary* lists both visits.
- [ ] *For Labour & Delivery* → *Labour & Partograph* tab; adding partograph rows draws the chart; a 3 cm row is rejected.
- [ ] Record *Mode of Delivery* + *Time of Delivery (Baby)* + a baby row → the Pregnancy Episode becomes *Delivered*.
- [ ] **/app/maternity-desk** shows today's attendances, women in labour and the register.

**Insurance**
- [ ] On an NHIS encounter (as insurance_smu): *Insurance Claim → NHIS Claim Form* prints; *Claim-it XML* downloads.
- [ ] The banner shows the claim total and any problems (missing CCC, codes…).
- [ ] On a corporate encounter: *Corporate Claim Summary* prints with insurance / co-pay columns.
- [ ] **/app/insurance-claims**: filter this month → totals; *Claim-it XML (all NHIS)*; *Print all*; *Set status of selected*.

---

## 11. Optional extras (not required, left out to keep changes minimal)

These were in my first version. They're purely cosmetic, so I removed them from the required steps. Add any of them later in the desk UI:

- Friendlier labels on the existing ANC fields (many show raw fieldnames, e.g. `tested_for_HIV`) and a label on the delivery section (`section_break_qdhy` → "Delivery Record").
- Change some existing ANC fields from **Data** to **Autocomplete** with suggested values (same database column, no data change), e.g. `mode_of_delivery`, `presentation`, `urine_protein`, `membranes`, `liquor`.
- Column Breaks inside the ANC sections for a two- or three-column layout.
- **Baby Form**: tick *In List View* on Sex, Birth Weight, Apgar 1/5 min and Vit K so the baby grid shows them; add *Time of Birth* and an *Outcome* select.
- **Pregnancy Episode**: Naming `format:ANC-{YYYY}-{#####}` (readable IDs instead of random hashes), Title Field `patient_name` with *Show Title in Link Fields*.
- Code doctypes: Title Field = the code field + *Show Title in Link Fields*, so G-DRG links show the code instead of a hash.

---

## 12. Rollback

1. Revert the 4 hand-edited files (or `git checkout` them).
2. Remove the two entries from `doctype_js` in `hooks.py` first. That alone switches off all the new client behaviour.
3. Delete the copied folders and files from Section 6 and the 5 doctype folders from Section 2, then `bench migrate`.
4. The new fields on `patient_encounter`, `Pregnancy Episode` and the code doctypes are additive. Leave them, or delete them in the DocType editor.
