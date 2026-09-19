import 'package0:flutter/material.dart';

void main() {
  runApp(const NestingApp());
}

class NestingApp extends StatelessWidget {
  const NestingApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Раскрой Металла',
      theme: ThemeData(primarySwatch: Colors.blueGrey),
      home: const NestingCanvasScreen(),
    );
  }
}

class NestingCanvasScreen extends StatelessWidget {
  const NestingCanvasScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Карта раскроя: Лист 1 (2500x1250)'),
        actions: [
          IconButton(icon: const Icon(Icons.save), onPressed: () {}),
        ],
      ),
      body: InteractiveViewer(
        boundaryMargin: const EdgeInsets.all(double.infinity),
        minScale: 0.1,
        maxScale: 5.0,
        constrained: false, 
        child: Container(
          padding: const EdgeInsets.all(50),
          child: CustomPaint(
            size: const Size(2500, 1250),
            painter: NestingPainter(),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.calculate),
        tooltip: 'Сформировать КП',
      ),
    );
  }
}

class NestingPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final sheetPaint = Paint()
      ..color = Colors.grey.shade300
      ..style = PaintingStyle.fill;
    
    final borderPaint = Paint()
      ..color = Colors.black
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke;

    final sheetRect = Rect.fromLTWH(0, 0, size.width, size.height);
    canvas.drawRect(sheetRect, sheetPaint);
    canvas.drawRect(sheetRect, borderPaint);

    final partPaint = Paint()
      ..color = Colors.green.withOpacity(0.7)
      ..style = PaintingStyle.fill;
      
    final partBorder = Paint()
      ..color = Colors.green.shade900
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final part1 = Rect.fromLTWH(50, 50, 400, 300);
    canvas.drawRect(part1, partPaint);
    canvas.drawRect(part1, partBorder);

    final center = const Offset(600, 200);
    canvas.drawCircle(center, 150, partPaint);
    canvas.drawCircle(center, 150, partBorder);
    
    canvas.drawCircle(center, 80, sheetPaint);
    canvas.drawCircle(center, 80, partBorder);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
