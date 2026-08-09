export 'unsupported_connection.dart'
  if (dart.library.ffi) 'native_connection.dart'
  if (dart.library.html) 'web_connection.dart';
