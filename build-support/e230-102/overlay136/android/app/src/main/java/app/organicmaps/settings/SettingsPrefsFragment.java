package app.organicmaps.settings;

import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.preference.Preference;
import androidx.appcompat.app.AlertDialog;

import app.organicmaps.BuildConfig;
import app.organicmaps.R;
import app.organicmaps.editor.ProfileActivity;
import app.organicmaps.help.HelpActivity;
import app.organicmaps.sdk.editor.OsmOAuth;
import java.io.File;
import java.text.DateFormat;
import java.util.Date;

public class SettingsPrefsFragment extends BaseXmlSettingsFragment
{
  private static final String CB6_DATA_INFO_KEY = "cb6_data_information";

  @Override
  public void onCreatePreferences(Bundle bundle, String root)
  {
    super.onCreatePreferences(bundle, root);
    if (root == null && getPreferenceScreen() != null && findPreference(CB6_DATA_INFO_KEY) == null)
    {
      Preference info = new Preference(requireContext());
      info.setKey(CB6_DATA_INFO_KEY);
      info.setTitle("CB6 データ情報");
      info.setSummary("信号機DBの状態・件数・更新日時");
      info.setOnPreferenceClickListener(pref -> { showCb6DataInformation(); return true; });
      getPreferenceScreen().addPreference(info);
    }
  }

  @Override
  protected int getXmlResources()
  {
    return R.xml.prefs_main;
  }

  @Override
  public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState)
  {
    super.onViewCreated(view, savedInstanceState);
  }

  @Override
  public void onResume()
  {
    super.onResume();
    updateProfileSettingsPrefsSummary();
    updateAboutSummary();
  }

  @Override
  public boolean onPreferenceTreeClick(Preference preference)
  {
    final String key = preference.getKey();
    if (key != null && key.equals(getString(R.string.pref_osm_profile)))
    {
      startActivity(new Intent(requireActivity(), ProfileActivity.class));
    }
    else if (key != null && key.equals(getString(R.string.pref_about)))
    {
      startActivity(new Intent(requireActivity(), HelpActivity.class));
    }
    return super.onPreferenceTreeClick(preference);
  }

  private void showCb6DataInformation()
  {
    new AlertDialog.Builder(requireContext())
        .setTitle("CB6 データ情報")
        .setMessage(readSignalDatabaseStatus(requireContext()))
        .setPositiveButton(android.R.string.ok, null)
        .show();
  }

  /** Read-only status: does not activate, import, or mutate a signal DB. */
  private static String readSignalDatabaseStatus(@NonNull Context context)
  {
    final String name;
    try
    {
      name = context.getSharedPreferences("cb6_signal_db", Context.MODE_PRIVATE)
          .getString("active_file", null);
    }
    catch (RuntimeException e)
    {
      return "信号機データ：設定を読み取れません" + "\\n\\nコンビニ6種：準備のみ（未実装）";
    }
    String stores = "\n\nコンビニ6種：準備のみ（未実装）";
    if (name == null || !name.matches("signals-[0-9a-f]{64}\\.sqlite"))
      return "信号機データ：未設定" + stores;
    File file = new File(new File(context.getFilesDir(), "cb6-signal-db"), name);
    if (!file.isFile()) return "信号機データ：ファイルなし" + stores;
    try (SQLiteDatabase db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
             SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS);
         Cursor c = db.rawQuery("SELECT COUNT(*) FROM signals", null))
    {
      if (!c.moveToFirst()) throw new IllegalStateException("Count unavailable");
      String modified = DateFormat.getDateTimeInstance().format(new Date(file.lastModified()));
      return "信号機データ：登録あり\n信号機件数：" + c.getLong(0)
          + " 件\n更新日時：" + modified + "\nDBバージョン：" + db.getVersion()
          + "\n状態：読み取り可能（描画は未検証）" + stores;
    }
    catch (Exception e) { return "信号機データ：読み取り不可" + stores; }
  }

  private void updateProfileSettingsPrefsSummary()
  {
    final Preference pref = getPreference(getString(R.string.pref_osm_profile));
    if (OsmOAuth.isAuthorized())
      pref.setSummary(OsmOAuth.getUsername());
    else
      pref.setSummary(R.string.not_signed_in);
  }

  private void updateAboutSummary()
  {
    final Preference pref = getPreference(getString(R.string.pref_about));
    pref.setSummary(getString(R.string.pref_about_summary, BuildConfig.VERSION_NAME));
  }
}
