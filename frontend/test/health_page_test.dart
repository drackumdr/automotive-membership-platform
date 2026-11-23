import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:membership_app/core/api/api_client.dart';
import 'package:membership_app/features/public/health_page.dart';

void main() {
  testWidgets('muestra estado del backend y la base de datos', (tester) async {
    final mock = MockClient((_) async =>
        http.Response('{"status":"ok","database":"ok"}', 200));
    await tester.pumpWidget(MaterialApp(home: HealthPage(api: ApiClient(client: mock))));
    await tester.pumpAndSettle();
    expect(find.text('Backend: ok'), findsOneWidget);
    expect(find.text('Base de datos: ok'), findsOneWidget);
  });
}
