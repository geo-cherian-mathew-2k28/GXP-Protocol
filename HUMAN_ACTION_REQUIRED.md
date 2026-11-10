# Human action required

Nothing in this file authorizes public deployment, registrations, purchases, or
legal submissions. Complete these actions before a public or production release.

## 1. Confirm name, trademark, domain, and repository naming

- **Why:** `GXP` and `gxp` are provisional; a technical implementation does not
  establish trademark rights or name availability.
- **Where:** An intellectual-property professional for the intended
  jurisdictions, plus the relevant national/regional trademark databases and a
  domain registrar of your choice.
- **What to bring:** Intended classes of goods/services, project description,
  candidate names, jurisdictions, and the proposed logo/domain names.
- **Steps:** Obtain clearance advice; decide the ownership entity; register a
  domain only after approval; retain search results, advice, receipts, and
  registration evidence.
- **Possible fees/approvals:** Search, legal advice, filings, and registrations
  vary by jurisdiction.
- **What the project can prepare:** Product description, architecture documents,
  and a list of candidate names.

## 2. Select a software licence and copyright owner

- **Why:** The repository currently grants no licence. A public project needs an
  owner-approved licence and contribution policy.
- **Where:** Consult an appropriately qualified legal adviser; compare the
  official licence texts for the shortlisted licence.
- **What to bring:** Whether commercial adopters, patent grants, copyleft, and
  contributor agreements are acceptable.
- **Steps:** Identify the copyright owner; choose and approve a licence; replace
  `LICENSE`; update `CONTRIBUTING.md`, package metadata, and release guidance;
  retain the written approval.
- **Possible fees/approvals:** Legal review may cost money; approval is an owner
  decision.
- **What the project can prepare:** A licence comparison, once the desired
  distribution model is specified.

## 3. Decide whether to register `gxp` as a URI scheme

- **Why:** Implementing `gxp://` does not register it. The IANA registry lists
  its own process and references RFC 7595.
- **Where:** Review the [IANA URI Schemes registry](https://www.iana.org/assignments/uri-schemes)
  and [RFC 7595 section 7](https://www.rfc-editor.org/rfc/rfc7595.html#section-7).
- **What to bring:** A stable public scheme specification, contact information,
  security/privacy considerations, and evidence that the name is available.
- **Steps:** Search the registry; prepare the RFC 7595 registration template;
  arrange the required review for the selected registration type; submit in your
  own name only after legal and technical review; save the submission and
  registry result.
- **Possible fees/approvals:** IANA's process is administrative, but review and
  organisational approval are required; do not assume an outcome or fee without
  checking at submission time.
- **What the project can prepare:** The draft URI specification in this repo.

## 4. Provision a real pilot environment and device identity

- **Why:** The reference server must not be Internet-exposed. Production needs a
  device registry, mTLS/certificates or an equivalent approved identity system,
  protected keys, a broker/API endpoint, and operator access controls.
- **Where:** Your chosen cloud/on-premises platform, PKI/CA service, mobile
  carrier, and hardware vendor.
- **What to bring:** Fleet size, threat model, data-retention policy, data
  residency requirements, network and hardware details.
- **Steps:** Approve the architecture; create accounts and network boundaries;
  use unique credentials; enrol a controlled pilot cohort; test revocation,
  rotation, backup/recovery, and incident response; retain configuration and
  audit evidence.
- **Possible fees/approvals:** Infrastructure, SIM/data, CA/HSM, hardware, and
  deployment permissions may apply.
- **What the project can prepare:** Deployment configuration and test plans once
  the platform and scale are chosen.

## 5. Obtain pilot, privacy, and operational approval

- **Why:** Bus location data can expose movement patterns, and hardware on buses
  may require operator, safety, labour, and data-protection review.
- **Where:** Fleet owner/operator, legal/privacy team, security team, and local
  regulator where applicable.
- **Steps:** Approve data purpose, retention, access controls, device mounting,
  permitted commands, test route, escalation path, and rollback; collect written
  approvals before installation.
- **Evidence:** Approved DPIA/privacy assessment if required, safety review,
  change tickets, device inventory, and signed pilot acceptance.

