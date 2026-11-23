import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';

class HealthPage extends StatefulWidget {
  const HealthPage({super.key, this.api});
  final ApiClient? api;

  @override
  State<HealthPage> createState() => _HealthPageState();
}

class _HealthPageState extends State<HealthPage> {
  late final ApiClient _api = widget.api ?? ApiClient();
  String _backend = 'verificando...';
  String _database = 'verificando...';

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    try {
      final r = await _api.getJson('/health');
      setState(() {
        _backend = r['status'] as String? ?? 'desconocido';
        _database = r['database'] as String? ?? 'desconocido';
      });
    } catch (_) {
      setState(() {
        _backend = 'sin conexión';
        _database = 'desconocido';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Plataforma de Membresías')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Backend: $_backend', key: const Key('backend-status')),
            const SizedBox(height: 8),
            Text('Base de datos: $_database', key: const Key('database-status')),
            const SizedBox(height: 16),
            FilledButton(onPressed: _check, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }
}
