import { useEffect, useState } from 'react'
import type { Lang } from '../lib/types'
import { verifyChain, type VerificationResult } from '../lib/chainVerifier'
import '../styles/parts/trust.css'

type TrustTab = 'overview' | 'accuracy' | 'ledger' | 'methodology' | 'limitations' | 'models' | 'api'

const L = {
  hi: {
    title: 'प्रहरी पारदर्शिता और भरोसा',
    subtitle: 'सार्वजनिक ऑडिट, क्रिप्टोग्राफ़िक खाता और भौतिकी मॉडल की पूरी जानकारी',
    back: '← वापस ऐप पर जाएँ',
    tabs: {
      overview: 'अवलोकन',
      accuracy: 'सटीकता',
      ledger: 'खाता सत्यापन (Ledger)',
      methodology: 'कार्यप्रणाली',
      limitations: 'सीमाएँ',
      models: 'रोग मॉडल',
      api: 'डेटा और API',
    },
    ledger: {
      title: 'क्रिप्टोग्राफ़िक अलर्ट लेज़र (In-Browser SHA-256 Verifier)',
      desc: 'यह सत्यापन सीधे आपके ब्राउज़र में चलता है। हर अलर्ट पिछली प्रविष्टि से SHA-256 हैश द्वारा जंजीर की तरह जुड़ा है। यदि सर्वर पर एक भी बाइट बदला जाए तो जंजीर तुरंत टूट जाती है।',
      verifyBtn: 'लेज़र पुनः जाँचे',
      verifying: 'जंजीर की गणना हो रही है…',
      validChain: '✓ पूरी लेज़र जंजीर वैध है — कोई छेड़छाड़ नहीं पाई गई',
      brokenChain: '✗ लेज़र जंजीर टूटी हुई है!',
      entriesCount: 'सत्यापित प्रविष्टियाँ',
      tamperTest: 'छेड़छाड़ परीक्षण (Simulate Tamper)',
      tamperDesc: 'जाँचें कि क्या ब्राउज़र एक नकली या बदले हुए रिकॉर्ड को तुरंत पकड़ता है:',
      tamperBtn: 'एक बाइट बदलकर देखें',
      restoreBtn: 'मूल लेज़र बहाल करें',
      tableHead: { time: 'समय / Run', cell: 'सेल / क्षेत्र', band: 'बैंड', risk: 'जोखिम', hash: 'SHA-256 हैश', prevHash: 'पिछला हैश' },
      empty: 'इस रन में कोई अलर्ट जारी नहीं हुआ — खाता खाली है (जंजीर में जोड़ने को कुछ नहीं)।',
    },
    accuracy: {
      title: 'सटीकता और आर्थिक संतुलन (§35.4)',
      asymmetryTitle: 'गलत अलार्म बनाम छूटा हुआ प्रकोप (Economic Asymmetry)',
      asymmetryBody: 'एक छोटे किसान के लिए एक बार अनावश्यक छिड़काव का खर्च लगभग ₹800/एकड़ है, जबकि आलू झुलसा रोग से पूरी फसल नष्ट होने पर ₹50,000/एकड़ का नुकसान होता है (~62× अंतर)। इसलिए हमारी प्रणाली अत्यधिक सतर्कता (Sensitivity > 95%) के साथ ट्यून की गई है।',
      statusTitle: 'हिंडकास्ट सत्यापन स्थिति',
      statusBody: 'नीचे दिए मान हमारे डिज़ाइन लक्ष्य हैं, मापे गए परिणाम नहीं। इन्हें सत्यापित करने के लिए पुराने प्रकोप के लेबल-युक्त डेटा (हिंडकास्ट) की ज़रूरत है, जो अभी नहीं चलाया गया — इसलिए हम कोई मनगढ़ंत सटीकता संख्या नहीं, बल्कि ईमानदारी से लक्ष्य दिखाते हैं।',
      metricTarget: 'संवेदनशीलता लक्ष्य (Sensitivity target)',
      targetVal: '≥ 95%',
      farTarget: 'गलत अलार्म दर लक्ष्य (FAR operating target)',
      farVal: '≤ 0.60',
    },
    limitations: {
      title: 'प्रणाली की सीमाएँ (Transparent Limitations §34.3)',
      items: [
        { head: '1 km गणना ग्रिड (Computation vs Measurement)', body: '1 वर्ग किमी का मौसम मॉडल भौतिकी के आधार पर सूक्ष्म-जलवायु का अनुमान लगाता है, न कि हर खेत में लगे मौसम स्टेशन का वास्तविक माप।' },
        { head: 'पत्तियों का गीलापन प्रॉक्सी (RH as Proxy)', body: 'पत्ते के गीले रहने का समय वायुमंडलीय सापेक्ष आर्द्रता (RH ≥ 90%) और ओस बिंदु से आंका जाता है, सेंसर से सीधे नहीं।' },
        { head: 'दवा का नाम न बताना (Zero Chemical Prescription)', body: 'यह ऐप किसी रसायन, दवा या खुराक की सिफारिश नहीं करता। यह केवल छिड़काव के सुरक्षित और सटीक समय की गणना करता है।' },
      ],
    },
    models: {
      title: 'सत्यापित वैज्ञानिक मॉडल (Cited Agronomy Models)',
      lateBlight: 'आलू पछेती झुलसा (Potato Late Blight — Phytophthora infestans)',
      lateBlightDesc: 'हटन मापदंड (Hutton Criteria 1956) और वॉलिन DSV (Wallin 1962, BLITECAST)। 2 दिन लगातार नमी और तापमान सीमा पूरी होने पर चेतावनी।',
      earlyBlight: 'आलू अगेती झुलसा (Potato Early Blight — Alternaria solani)',
      earlyBlightDesc: 'टॉमकास्ट DSV मॉडल (TOMCAST Pitblado 1992 / Madden 1978)। फफूंद संक्रमण के लिए पत्ती के गीलेपन और औसत तापमान पर आधारित।',
      citation: 'संदर्भ:',
    },
  },
  en: {
    title: 'PRAHARI Trust & Transparency',
    subtitle: 'Public audit, cryptographic alert ledger, and physical disease model catalog',
    back: '← Back to Farmer App',
    tabs: {
      overview: 'Overview',
      accuracy: 'Accuracy',
      ledger: 'Ledger Verifier',
      methodology: 'Methodology',
      limitations: 'Limitations',
      models: 'Disease Models',
      api: 'Data & API',
    },
    ledger: {
      title: 'Cryptographic Alert Ledger (In-Browser SHA-256 Verifier)',
      desc: 'This verification executes entirely in your browser using the Web Crypto API. Every alert entry is chained to the previous record via SHA-256. Tampering with any historical record breaks the entire subsequent chain.',
      verifyBtn: 'Re-verify Ledger',
      verifying: 'Verifying hash chain…',
      validChain: '✓ Entire ledger chain verified — Zero tampering detected',
      brokenChain: '✗ Ledger chain verification failed!',
      entriesCount: 'Verified Records',
      tamperTest: 'Interactive Tamper Simulation',
      tamperDesc: 'Test whether the in-browser verifier immediately detects a modified record:',
      tamperBtn: 'Inject 1-Byte Tamper',
      restoreBtn: 'Restore Genuine Ledger',
      tableHead: { time: 'Run Time', cell: 'Cell / Scope', band: 'Band', risk: 'Risk', hash: 'SHA-256 Hash', prevHash: 'Previous Hash' },
      empty: 'No alerts were issued in this run, so the ledger is empty (nothing to chain).',
    },
    accuracy: {
      title: 'Accuracy & Economic Asymmetry (§35.4)',
      asymmetryTitle: 'False Alarm vs Missed Outbreak (~62× Economic Asymmetry)',
      asymmetryBody: 'For a smallholder potato farmer, a false alarm (unneeded preventive spray) costs ~₹800/acre, while a missed late blight outbreak destroys the entire harvest causing ~₹50,000/acre loss (~62× difference). Hence, PRAHARI operates at a high-sensitivity operating point (Sensitivity > 95%).',
      statusTitle: 'Hindcast Validation Status',
      statusBody: 'The numbers below are our design targets, not measured results. Validating them needs labelled historical outbreak data (a hindcast), which we have not run yet — so we show the targets honestly rather than invent an accuracy figure.',
      metricTarget: 'Sensitivity target',
      targetVal: '≥ 95%',
      farTarget: 'False-alarm-rate operating target',
      farVal: '≤ 0.60',
    },
    limitations: {
      title: 'Transparent Limitations (PRD §34.3 / §18.4)',
      items: [
        { head: '1 km Computation Grid (Computation, Not Measurement)', body: '1 km grid represents physical downscaling and lapse-rate interpolation of Numerical Weather Prediction, not individual in-situ farm stations.' },
        { head: 'RH as Leaf Wetness Proxy', body: 'Leaf wetness duration is derived from atmospheric relative humidity (RH ≥ 90%) and Magnus-formula dewpoint, not physical leaf wetness sensors.' },
        { head: 'Zero Chemical Prescriptions', body: 'The engine computes precise microclimate timing windows only. It strictly never recommends chemical brands, doses, or tank mixes.' },
      ],
    },
    models: {
      title: 'Peer-Reviewed Scientific Models',
      lateBlight: 'Potato Late Blight (Phytophthora infestans — Oomycete)',
      lateBlightDesc: 'Hutton Criteria (Smith 1956) + Wallin Disease Severity Values (Wallin 1962, BLITECAST Krause et al. 1975). Severity-gated risk bands with lapse-rate corrections.',
      earlyBlight: 'Potato Early Blight (Alternaria solani — Fungus)',
      earlyBlightDesc: 'TOMCAST DSV Model (Pitblado 1992, Madden et al. 1978). Evaluates fungal spore germination from leaf wetness and temperature duration.',
      citation: 'Citation:',
    },
  },
}

export function TrustScreen({
  lang,
  onClose,
  view = 'farrukhabad_blight_outbreak',
}: {
  lang: Lang
  onClose: () => void
  view?: string
}) {
  const [tab, setTab] = useState<TrustTab>('ledger')
  const [ledgerRaw, setLedgerRaw] = useState<string>('')
  const [tamperedRaw, setTamperedRaw] = useState<string | null>(null)
  const [verifying, setVerifying] = useState<boolean>(false)
  const [result, setResult] = useState<VerificationResult | null>(null)
  const t = L[lang]

  useEffect(() => {
    async function loadLedger() {
      setVerifying(true)
      try {
        const scenarioFolder = view === 'farrukhabad' ? 'farrukhabad' : view
        const res = await fetch(`/artefacts/${scenarioFolder}/ledger.jsonl`)
        if (res.ok) {
          const text = await res.text()
          setLedgerRaw(text)
          // An empty file is the honest signal that no alerts fired this run — not an error,
          // and never a place to substitute a fabricated "sample" chain.
          setResult(text.trim() ? await verifyChain(text) : null)
        } else {
          setLedgerRaw('')
          setResult(null)
        }
      } catch {
        setLedgerRaw('')
        setResult(null)
      } finally {
        setVerifying(false)
      }
    }
    loadLedger()
  }, [view])

  async function handleTamper() {
    if (!ledgerRaw) return
    const lines = ledgerRaw.split('\n').filter(Boolean)
    if (lines.length > 2) {
      const target = JSON.parse(lines[2])
      // Flip a REAL, hash-covered field — the kind of tamper that matters: silently downgrading
      // a fired alert. The chain must catch it at this exact entry.
      target.band = target.band === 'safe' ? 'act' : 'safe'
      lines[2] = JSON.stringify(target)
      const tampered = lines.join('\n')
      setTamperedRaw(tampered)
      setVerifying(true)
      const v = await verifyChain(tampered)
      setResult(v)
      setVerifying(false)
    }
  }

  async function handleRestore() {
    setTamperedRaw(null)
    if (!ledgerRaw) return
    setVerifying(true)
    const v = await verifyChain(ledgerRaw)
    setResult(v)
    setVerifying(false)
  }

  return (
    <div className="trust-page">
      <header className="trust-page__header">
        <div className="trust-page__header-inner">
          <button className="trust-page__back-btn" onClick={onClose}>
            {t.back}
          </button>
          <h1 className="trust-page__title">{t.title}</h1>
          <p className="trust-page__subtitle">{t.subtitle}</p>
        </div>

        <nav className="trust-page__tabs" aria-label="Trust Navigation">
          {(Object.keys(t.tabs) as TrustTab[]).map((tabKey) => (
            <button
              key={tabKey}
              className={`trust-tab-btn ${tab === tabKey ? 'trust-tab-btn--active' : ''}`}
              onClick={() => setTab(tabKey)}
            >
              {t.tabs[tabKey]}
            </button>
          ))}
        </nav>
      </header>

      <main className="trust-page__content">
        {/* LEDGER TAB */}
        {tab === 'ledger' && (
          <section className="trust-card">
            <div className="trust-card__header">
              <h2>{t.ledger.title}</h2>
              <p>{t.ledger.desc}</p>
            </div>

            <div className="trust-status-banner">
              {verifying ? (
                <div className="trust-status trust-status--loading">
                  <span className="spinner" aria-hidden="true" />
                  <span>{t.ledger.verifying}</span>
                </div>
              ) : !result ? (
                <div className="trust-status trust-status--loading">
                  <span className="trust-status__icon">📭</span>
                  <div>
                    <strong>{t.ledger.empty}</strong>
                  </div>
                </div>
              ) : result.ok ? (
                <div className="trust-status trust-status--success">
                  <span className="trust-status__icon">🛡️</span>
                  <div>
                    <strong>{t.ledger.validChain}</strong>
                    <p>{t.ledger.entriesCount}: {result.count} blocks</p>
                  </div>
                </div>
              ) : (
                <div className="trust-status trust-status--error">
                  <span className="trust-status__icon">⚠️</span>
                  <div>
                    <strong>{t.ledger.brokenChain}</strong>
                    <p>{result?.reason}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Tamper testing panel — only meaningful when a real, non-empty chain is loaded. */}
            {ledgerRaw && (
              <div className="trust-tamper-box">
                <h3>{t.ledger.tamperTest}</h3>
                <p>{t.ledger.tamperDesc}</p>
                <div className="trust-tamper-actions">
                  {!tamperedRaw ? (
                    <button className="btn btn--danger" onClick={handleTamper}>
                      ⚡ {t.ledger.tamperBtn}
                    </button>
                  ) : (
                    <button className="btn btn--primary" onClick={handleRestore}>
                      🔄 {t.ledger.restoreBtn}
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Ledger entries preview */}
            <div className="trust-table-wrapper">
              <table className="trust-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t.ledger.tableHead.time}</th>
                    <th>{t.ledger.tableHead.cell}</th>
                    <th>{t.ledger.tableHead.band}</th>
                    <th>{t.ledger.tableHead.hash}</th>
                    <th>{t.ledger.tableHead.prevHash}</th>
                  </tr>
                </thead>
                <tbody>
                  {(result?.entries || []).slice(0, 15).map((entry, idx) => (
                    <tr key={idx} className={tamperedRaw && idx === 2 ? 'tr-tampered' : ''}>
                      <td>{entry.seq ?? idx}</td>
                      <td><span className="mono">{(entry.timestamp || '').replace('T', ' ').slice(0, 16)}</span></td>
                      <td className="mono">{entry.cell_id}</td>
                      <td>
                        <span className={`badge badge--${entry.band || 'safe'}`}>
                          {(entry.band || '').toUpperCase()}
                        </span>
                      </td>
                      <td className="mono text-truncate" title={entry.hash}>{entry.hash?.slice(0, 18)}…</td>
                      <td className="mono text-truncate" title={entry.prev_hash}>{entry.prev_hash?.slice(0, 18)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ACCURACY TAB */}
        {tab === 'accuracy' && (
          <section className="trust-card">
            <h2>{t.accuracy.title}</h2>
            <div className="trust-grid">
              <div className="trust-feature-box">
                <h3>⚖️ {t.accuracy.asymmetryTitle}</h3>
                <p>{t.accuracy.asymmetryBody}</p>
                <div className="asymmetry-metric-bar">
                  <div className="asymmetry-col false-alarm">
                    <span className="col-label">False Alarm</span>
                    <span className="col-val">~₹800/acre</span>
                    <span className="col-sub">1 preventive spray</span>
                  </div>
                  <div className="asymmetry-col missed-outbreak">
                    <span className="col-label">Missed Blight Outbreak</span>
                    <span className="col-val">~₹50,000/acre</span>
                    <span className="col-sub">100% crop loss (62× worse)</span>
                  </div>
                </div>
              </div>

              <div className="trust-feature-box">
                <h3>📊 {t.accuracy.statusTitle}</h3>
                <p>{t.accuracy.statusBody}</p>
                <div className="stats-row">
                  <div className="stat-card">
                    <span className="stat-num">{t.accuracy.targetVal}</span>
                    <span className="stat-label">{t.accuracy.metricTarget}</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-num">{t.accuracy.farVal}</span>
                    <span className="stat-label">{t.accuracy.farTarget}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* METHODOLOGY TAB */}
        {tab === 'methodology' && (
          <section className="trust-card">
            <h2>{lang === 'hi' ? 'भौतिकी आधारित कार्यप्रणाली (PRD §18.3)' : 'Physics-First Methodology (PRD §18.3)'}</h2>
            <div className="methodology-steps">
              <div className="method-step">
                <span className="step-num">1</span>
                <div>
                  <h4>{lang === 'hi' ? 'NWP मौसम डेटा और लैप्स-रेट सुधार' : 'NWP Weather & Elevation Lapse-Rate'}</h4>
                  <p>{lang === 'hi' ? 'Open-Meteo मौसम मॉडल (ECMWF, GFS) से 25-नोड जाली पर डेटा लिया जाता है। 6.5 °C/km लैप्स-रेट से तापमान और मैग्नस समीकरण द्वारा सापेक्ष आर्द्रता की पुनः गणना की जाती है।' : 'Atmospheric fields from Open-Meteo NWP models downscaled with a 6.5 °C/km environmental lapse rate and Magnus-formula RH recomputation.'}</p>
                </div>
              </div>
              <div className="method-step">
                <span className="step-num">2</span>
                <div>
                  <h4>{lang === 'hi' ? 'शुद्ध इंजन में रोग मापदंड गणना' : 'Pure AST-Enforced Disease Evaluation'}</h4>
                  <p>{lang === 'hi' ? 'इंजन में कोई नेटवर्क या घड़ी नहीं है। हटन (Hutton) और टॉमकास्ट (TOMCAST) वैज्ञानिक तालिकाओं से DSV मान तय होते हैं।' : 'Zero network/clock AST-enforced deterministic engine evaluating Hutton wet-spells and TOMCAST DSVs.'}</p>
                </div>
              </div>
              <div className="method-step">
                <span className="step-num">3</span>
                <div>
                  <h4>{lang === 'hi' ? 'सात छिड़काव द्वार (7 Spray Gates)' : 'Seven Agronomic Spray Gates'}</h4>
                  <p>{lang === 'hi' ? 'बारिश (वर्षा पूर्व/पश्चात), तेज़ हवा, शांत हवा, अत्यधिक गर्मी, अंधेरा और संक्रमण शुरू होने के समय की सख्त जाँच।' : 'Strict timing gates for rain wash-off, drift winds, thermal inversion, temperature scorch, and daylight.'}</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* LIMITATIONS TAB */}
        {tab === 'limitations' && (
          <section className="trust-card">
            <h2>{t.limitations.title}</h2>
            <div className="limitations-list">
              {t.limitations.items.map((item, i) => (
                <article key={i} className="limitation-item">
                  <h3><span aria-hidden="true">⚠️</span> {item.head}</h3>
                  <p>{item.body}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {/* MODELS TAB */}
        {tab === 'models' && (
          <section className="trust-card">
            <h2>{t.models.title}</h2>
            <div className="models-catalog">
              <article className="model-box">
                <header className="model-box__head">
                  <span className="badge badge--act">Oomycete</span>
                  <h3>{t.models.lateBlight}</h3>
                </header>
                <p>{t.models.lateBlightDesc}</p>
                <p className="model-citation"><strong>{t.models.citation}</strong> Hutton criteria; Wallin (1962); Smith (1956); BLITECAST (Krause et al. 1975)</p>
              </article>

              <article className="model-box">
                <header className="model-box__head">
                  <span className="badge badge--watch">Fungus</span>
                  <h3>{t.models.earlyBlight}</h3>
                </header>
                <p>{t.models.earlyBlightDesc}</p>
                <p className="model-citation"><strong>{t.models.citation}</strong> TOMCAST model; Madden et al. (1978); Pitblado (1992)</p>
              </article>
            </div>
          </section>
        )}

        {/* OVERVIEW / API TAB */}
        {(tab === 'overview' || tab === 'api') && (
          <section className="trust-card">
            <h2>{lang === 'hi' ? 'खुला डेटा और सत्यापन अनुबंध' : 'Open Data & API Contracts'}</h2>
            <p>{lang === 'hi' ? 'प्रहरी का सारा डेटा स्थिर GeoJSON फाइलों में प्रकाशित होता है। कोई छुपा हुआ सर्वर या बंद डेटाबेस नहीं है।' : 'All PRAHARI alerts and field payload artefacts are published as open, deterministic GeoJSON files.'}</p>
            <div className="code-snippet">
              <pre>
{`GET /artefacts/farrukhabad/today.geojson
GET /artefacts/farrukhabad/fields.json
GET /artefacts/farrukhabad/ledger.jsonl (Hash-chained append-only)`}
              </pre>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
