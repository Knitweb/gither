# License Protocol

Gither's core mirror rule is:

```text
mirror metadata by default
mirror code only when license records allow redistribution
execute or monetize only when the clause graph allows it
```

The first protocol snapshot includes the license templates offered by the GitHub and
GitLab APIs on 2026-06-22:

- GitHub `/licenses`: 13 templates.
- GitLab `/templates/licenses?per_page=100`: 46 templates.
- Union after key normalization: 46 templates.

GitLab's template set is broader than GitHub's and includes hardware, database,
documentation, font, European public-sector, Microsoft, and source-code licenses.
GitHub's offered templates are a subset of the union: AGPL-3.0, Apache-2.0,
BSD-2-Clause, BSD-3-Clause, BSL-1.0, CC0-1.0, EPL-2.0, GPL-2.0, GPL-3.0,
LGPL-2.1, MIT, MPL-2.0, and Unlicense.

## P2P Records

Gither should knit license data into the p2p forge as first-class records:

- `license_record`: normalized identity from GitHub, GitLab, SPDX, or custom text.
- `clause_record`: extracted obligations, restrictions, and definitions.
- `notice_record`: copyright, attribution, NOTICE, and full license text payloads.
- `consent_record`: maintainer approval beyond the public license.
- `mirror_manifest`: decision for catalog, archive, executable, and economic mirrors.

This means a p2p node can accept a repository object while still refusing to execute,
sell, or claim ownership over it.

## Mirror Classes

### Catalog Mirror

Always allowed for factual metadata:

- upstream URL;
- owner and repository name;
- commit hashes;
- detected license keys;
- stars, forks, and timestamps;
- SWHID or equivalent archive identifier when available.

### Code Archive Mirror

Allowed when the license permits redistribution and the mirror carries the required
notices.

Permissive licenses such as MIT, BSD, ISC, Apache-2.0, BSL-1.0, PostgreSQL, UPL, zlib,
CC0, 0BSD, MIT-0, and Unlicense are normally archive-safe.

### Reciprocal Archive Mirror

Allowed, but the mirror must keep source-disclosure and same-license obligations
visible.

This includes GPL, LGPL, MPL, EPL, EUPL, CeCILL, OSL, CERN-OHL reciprocal variants,
GFDL, ODbL, OFL, and similar licenses.

### Executable Mirror

Requires stricter checks:

- transitive dependencies;
- generated artifacts;
- NOTICE files;
- patent clauses;
- network-use clauses;
- file-level or library-level boundaries.

### Economic Mirror

Requires explicit policy approval.

Gither must not create ownership or royalty claims over third-party code unless the
license permits the economic action or the maintainer supplies a consent record.

## Clause Vocabulary

Gither breaks license text into reusable terms:

- `include-copyright`: preserve copyright and license notices.
- `document-changes`: mark modified files or derivative releases.
- `disclose-source`: provide corresponding source when distributing covered artifacts.
- `network-use-disclose`: network service use triggers source disclosure.
- `same-license`: derivatives or covered works stay under the same license.
- `same-license--file`: reciprocity applies per file.
- `same-license--library`: reciprocity applies to the covered library.
- `trademark-use`: no broad trademark rights are granted.
- `patent-use`: patent grant is absent, limited, or terminable.
- `managed-service-restriction`: hosted service use is restricted.
- `license-key-restriction`: changing license-key checks or feature-lock controls is
  restricted.
- `notice-preservation`: source-available and attribution notices remain visible.
- `field-of-use`: allowed use depends on purpose, user, revenue, scale, or environment.
- `change-date`: source-available license converts on a defined date.
- `no-selling`: paid distribution or substantially similar sale is restricted.
- `noncommercial`: commercial use is restricted.
- `source-available-not-open-source`: source can be viewed but the license is not an
  OSI-style open-source grant.

## Custom License Profiles

### Elastic License 2.0

Used by Elastic projects such as Elasticsearch and Kibana.

Gither clauses:

- `managed-service-restriction`;
- license-key or feature-unlocking restrictions;
- notice preservation;
- `source-available-not-open-source`.

Gither policy: catalog mirror is safe; code archive requires clause review; executable
or hosted-service mirrors require explicit permission.

### Server Side Public License 1.0

Used by MongoDB and other source-available server software.

Gither clauses:

- `network-use-disclose`;
- `managed-service-restriction`;
- `same-license`;
- `source-available-not-open-source`.

Gither policy: catalog and source archive can be recorded, but offering the software as
a service requires complete service-source compliance or maintainer consent.

### Business Source License 1.1

Used by MariaDB MaxScale and adopted by several infrastructure companies.

Gither clauses:

- `field-of-use`;
- `change-date`;
- `source-available-not-open-source`.

Gither policy: catalog mirror is safe; code archive must preserve the additional-use
grant, change date, and future change license; execution and monetization are blocked
until the allowed use is proven.

### Commons Clause

Used as an addendum by source-available commercial projects.

Gither clauses:

- `no-selling`;
- `source-available-not-open-source`.

Gither policy: catalog mirror is safe; code archive requires the underlying license and
the no-selling restriction; economic mirror is blocked.

### PolyForm Noncommercial 1.0.0

Used by projects that publish readable code but restrict commercial use.

Gither clauses:

- `noncommercial`;
- `field-of-use`;
- `source-available-not-open-source`.

Gither policy: noncommercial archive only; no Gither marketplace or royalty flow unless
there is a separate consent record.

## Current Command

```bash
gither license-protocol
gither license-protocol --json
```

The JSON output is intended to become the p2p payload for license-aware mirror nodes.
