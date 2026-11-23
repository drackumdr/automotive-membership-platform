import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';
import '../features/public/health_page.dart';

class MembershipApp extends StatelessWidget {
  const MembershipApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Plataforma de Membresías',
      theme: AppTheme.light,
      debugShowCheckedModeBanner: false,
      home: const HealthPage(),
    );
  }
}
