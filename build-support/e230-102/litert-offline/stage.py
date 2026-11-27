from pathlib import Path
import hashlib, shutil, sys, subprocess
HERE=Path(__file__).resolve().parent
ROOT=Path(sys.argv[1]).resolve()
APP=ROOT/'android/app'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    if s.count(a)!=1: raise ValueError('anchor: '+a)
    return s.replace(a,b,1)
def main():
    for n,h in EXPECTED.items():
        if digest(HERE/n)!=h: raise ValueError(n)
    places=HERE.parent/'ruri-offline/places.bin'
    if digest(places)!='f85101c3ac68484f7ff973108af89b1557fe4c962db7368e1ca7d52c91af1d54': raise ValueError('places.bin')
    fragment=APP/'src/main/java/app/organicmaps/search/SearchFragment.java'
    s=fragment.read_text()
    a=s.index('  private jp.cb6.search.Cb6SearchEngine aiCategoryEngine;')
    b=s.index('  private void startCustomSearch(String query)',a)
    old=s[a:b]
    if 'private void submitSearch()' not in old or 'consentDialog.show();' not in old: raise ValueError('search anchor')
    s=s[:a]+'''  private jp.cb6.search.Cb6LiteRtController lite;
  private android.widget.TextView liteStatus;

  private void cancelAiSearch() {
    if (lite != null) lite.cancel();
    if (liteStatus != null) liteStatus.setVisibility(View.GONE);
  }

  private void submitSearch() {
    if (getView() == null || lite == null) return;
    String input = getQuery().trim();
    if (input.isEmpty() || input.codePointCount(0,input.length()) > 128) return;
    runSearch(input);
    mSearchAdapter.requireVerifiedRows(true);
    final long ticket = mLastQueryTimestamp;
    Location fix = jp.cb6.search.AiSearch.recent(aiFix);
    liteStatus.setText("端末内で分類中…");
    liteStatus.setVisibility(View.VISIBLE);
    lite.start(input, fix, (rows, status) -> {
      if (getView() == null || ticket != mLastQueryTimestamp || liteStatus == null) return;
      mSearchAdapter.aiResults(rows, fix);
      liteStatus.setText(status);
    });
  }

'''+s[b:]
    s=replace(s,'    aiSearch = new jp.cb6.search.AiSearch(requireContext());','    aiSearch = new jp.cb6.search.AiSearch(requireContext());\n    lite = new jp.cb6.search.Cb6LiteRtController(requireContext());')
    s=replace(s,'    ((AppBarLayout) root.findViewById(R.id.app_bar)).addView(searchButton);','''    AppBarLayout appBar = root.findViewById(R.id.app_bar);
    appBar.addView(searchButton);
    liteStatus = new android.widget.TextView(requireContext());
    liteStatus.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
    liteStatus.setVisibility(View.GONE);
    appBar.addView(liteStatus);''')
    s=replace(s,'    if (consentDialog != null) consentDialog.dismiss();\n','')
    s=replace(s,'    aiSearch.close();','    if (lite != null) lite.close();\n    lite = null;\n    liteStatus = null;\n    aiSearch.close();')
    s=replace(s,'    searchButton.setContentDescription("検索（長押しでAPI設定）");','    searchButton.setContentDescription("検索");')
    s=replace(s,'    searchButton.setOnLongClickListener(v -> { aiSearch.configure(requireContext()); return true; });\n','')
    adapter=fragment.with_name('SearchAdapter.java')
    atext=adapter.read_text()
    atext=replace(atext,'  void begin(String q) {','  private boolean verifiedOnly;\n  void requireVerifiedRows(boolean active) {\n    verifiedOnly = active;\n    refreshData(mResults);\n  }\n  void begin(String q) {\n    verifiedOnly = false;')
    atext=replace(atext,'    java.util.List<jp.cb6.search.Cb6SearchEngine.Result> places = custom;', '    if (verifiedOnly) {\n      rows = Cb6SearchRows.merge(query, new SearchResult[0], online);\n      if (origin != null) rankNearby();\n      notifyDataSetChanged();\n      return;\n    }\n    java.util.List<jp.cb6.search.Cb6SearchEngine.Result> places = custom;')
    gradle=APP/'build.gradle'; g=gradle.read_text()
    g=replace(g,'\ndependencies {','\ndependencies {\n    implementation files("libs/litert-1.4.2.aar", "libs/litert-api-1.4.2.aar")')
    assets=APP/'src/main/assets/cb6_litert'; libs=APP/'libs'; java=APP/'src/main/java/jp/cb6/search'
    copies=[(HERE/n,assets/n) for n in ['fg_model.tflite','categories.tsv','all_label_terms.tsv']]+[(places,assets/'places.bin')]+[(HERE/n,libs/n) for n in ['litert-1.4.2.aar','litert-api-1.4.2.aar']]+[(f,java/f.name) for f in HERE.glob('*.java')]
    for _,dst in copies:
        if dst.exists(): raise FileExistsError(dst)
    if '--check' in sys.argv: return
    for src,dst in copies:
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    fragment.write_text(s); adapter.write_text(atext); gradle.write_text(g)

EXPECTED = {'litert-1.4.2.pom': '9528ce669b5bb545a03cd14d92f429064af04a644f2cd8e306e7705e8bf40a30', 'Cb6NgramEncoder.java': '99f1d7f9345f65e6fcae968dc53a6f12b554bd1a372e3946f8ddf612ee1f7b95', 'Cb6LiteRtController.java': '246160b1b5dbaa14ac61efa30eb2fd6ef469f9819fec9e81dbd6cead4e3969a4', 'litert-api-1.4.2.pom': 'da9af6af75d05c7af53571cf45833fdbd80271a99306b397090dac199c38c0d8', 'Cb6PlaceIndex.java': '9d32fe78bd42495b46d6b76d435d57a1ae9f4da414dd352277da204d18082118', 'Cb6CategoryDictionary.java': 'bc0abb4b06e50367f2f17373dc092f4234ed4fb6934025faddf8d04cd84519c4', 'litert-api-1.4.2.aar': '66c2ba8086bd5cbf89bec2bd81c3de6c1a852312829cd55bc30c9dd26ffa357c', 'Cb6CategoryResolver.java': 'b79bd13a5891ed894cf683cc103386bc1f5022d484ae10b58872240a653d9572', 'all_label_terms.tsv': '968aeb7488126db7e0125b4e51870b2e9252ef974e075300c6a00985eff4a428', 'litert-1.4.2.aar': '9b02cdf9db0a698b341b59e75c54ab8221d6304577cc43830d01024caf1fca74', 'Cb6SqliteLookup.java': '7a14c6e76d8123f1032a87a23977694766312e3b557171ba0c286768af342b50', 'fg_model.tflite': 'aa7baf1680aa70aef245eb4f57ac19b908e4137f5eebf82b249f88b6f3a62de9', 'Cb6QueryConstraintParser.java': '4754c4ce9e5238fd2381f1fca654bc16ec5eade536782fb3fca2a0264e64bf27', 'Cb6LiteRtSearch.java': '185e986c78ef9abe27c5fbb8d4735a7454fb947d5d86037ced913577b3c3f415', 'categories.tsv': 'e394297af46b87b99f8da37ceab5d9e578633c0e0a29b179d8e82a2d96401d9c'}
if __name__ == "__main__": main()
