import 'dart:convert';

import 'package:http/http.dart' as http;

/// URL del backend; se cambia con --dart-define=API_BASE_URL=https://...
const String apiBaseUrl =
    String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;

  Future<Map<String, dynamic>> getJson(String path) async {
    final res = await _client.get(Uri.parse('$apiBaseUrl$path'));
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return {...body, '_statusCode': res.statusCode};
  }
}
