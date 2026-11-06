#include <jni.h>
#include <cerrno>
#include <fcntl.h>
#include <sys/syscall.h>
#include <unistd.h>

#ifndef RENAME_NOREPLACE
#define RENAME_NOREPLACE (1U << 0)
#endif

// Candidate only. Return 0 or positive errno; never fall back to replacing rename().
extern "C" JNIEXPORT jint JNICALL
Java_app_organicmaps_cb6_signals_VerifiedPackageStager_nativeRenameNoReplace(
    JNIEnv * env, jclass, jstring source, jstring destination)
{
  if (!source || !destination) return EINVAL;
  char const * src = env->GetStringUTFChars(source, nullptr);
  if (!src) return ENOMEM; // A pending JNI exception may also be present.
  char const * dst = env->GetStringUTFChars(destination, nullptr);
  if (!dst)
  {
    env->ReleaseStringUTFChars(source, src);
    return ENOMEM;
  }
  int result;
#if defined(SYS_renameat2)
  result = syscall(SYS_renameat2, AT_FDCWD, src, AT_FDCWD, dst, RENAME_NOREPLACE);
  int error = result == 0 ? 0 : errno;
#else
  int error = ENOSYS;
#endif
  env->ReleaseStringUTFChars(destination, dst);
  env->ReleaseStringUTFChars(source, src);
  return error;
}
