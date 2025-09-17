### JC Based Consumption

ERPNext için İş Kartı (Job Card) bazlı tüketim uygulaması.

Bu uygulama varsayılan **Job Card → on_submit** davranışını override eder:

- Eğer **Üretim Ayarları > İş Kartı ve Kapasite Planlama > İş Kartı Bazlı Tüketim** işaretliyse:
  - İş Kartı'ndan doğrudan **Malzeme Tüketim** ve **Üretim Stok Girişlerini** oluşturur.
  - Tüketim ve üretim miktarlarını her bir İş Kartı bazında takip eder.
- Eğer işaretli değilse:
  - **ERPNext’in varsayılan davranışı** çalışır.

✅ **ERPNext v15.x.x (develop branch, commit 29197af)** üzerinde geliştirilmiş ve test edilmiştir.

---

### Kurulum

Bu uygulamayı [bench](https://github.com/frappe/bench) CLI kullanarak yükleyebilirsiniz:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app jc_based_consumption
```

---

### Katkıda Bulunma

Bu uygulama kod formatlama ve linting için `pre-commit` kullanır. Lütfen [pre-commit yükleyin](https://pre-commit.com/#installation) ve bu depo için aktif edin:

```bash
cd apps/jc_based_consumption
pre-commit install
```

Pre-commit aşağıdaki araçları kullanacak şekilde yapılandırılmıştır:

- ruff
- eslint
- prettier
- pyupgrade

---

### Lisans

MIT
