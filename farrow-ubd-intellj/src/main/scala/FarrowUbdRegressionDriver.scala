import java.io.{File, PrintWriter}
import java.nio.file.{Files, Paths}
import scala.collection.immutable.ListSet
import scala.jdk.CollectionConverters.IteratorHasAsScala

object FarrowUbdRegressionDriver extends App {

  val programs =
    Files
      .list(Paths.get("/home/amir/workspace/random-farrow-ubd-program"))
      .iterator()
      .asScala
      .filter(path => path.toString.endsWith(".program"))
      .map(_.toString)
      .toSeq
      .sortBy(p => Paths.get(p).getFileName.toString.stripSuffix(".program").toInt)

  val factories: Seq[(String, M_FARROW_UBD_TREE => (Module, () => Seq[String]))] = Seq(
    ("dynamic", tree => { val m = new M_FARROW_UBD_DYNAMIC[T_FARROW_UBD_TREE]("FarrowUbd", tree); (m, () => m.v_program_errs(m.t_Program.nodes(0)).asInstanceOf[ListSet[String]].toSeq) }),
    ("static",  tree => { val m = new M_FARROW_UBD_STATIC[T_FARROW_UBD_TREE]("FarrowUbd", tree); (m, () => m.v_program_errs(m.t_Program.nodes(0)).asInstanceOf[ListSet[String]].toSeq) }),
    ("synth",   tree => { val m = new M_FARROW_UBD_SYNTH[T_FARROW_UBD_TREE]("FarrowUbd", tree); (m, () => m.v_program_errs(m.t_Program.nodes(0)).asInstanceOf[ListSet[String]].toSeq) })
  )

  for ((moduleName, factory) <- factories) {
    println(f"Module: $moduleName")
    val output = s"/home/amir/workspace/random-farrow-ubd-program/$moduleName"
    var timings = List.empty[(String, Double)]

    for (program <- programs) {
      println(f"Running against ${program}")
      val ss = new FarrowUbdScanner(new java.io.FileReader(program));
      val sp = new FarrowUbdParser();
      sp.reset(ss, program);
      if (!sp.yyparse()) {
        println("Errors found.\n");
        System.exit(1);
      }

      val farrow_ubd_tree = sp.getTree();
      val p = farrow_ubd_tree.t_Program;

      val start = System.nanoTime()

      val (m_farrow_ubd, getResult) = factory(farrow_ubd_tree)

      // Debug.activate();

      farrow_ubd_tree.finish();
      m_farrow_ubd.finish();

      val end = System.nanoTime()

      val diff = end - start
      val seconds = diff / 1_000_000_000.0
      println(s"Seconds ${seconds}")

      timings :+= (Paths.get(program).getFileName.toString, seconds)

      val writer = new PrintWriter(new File(f"$output/${Paths.get(program).getFileName}.output"))
      val result = getResult()

      writer.write(result.mkString("\n"))
      writer.close()
    }

    val logWriter = new PrintWriter(new File(s"$output/timing-${moduleName}.log"))
    timings.foreach { case (name, secs) => logWriter.println(f"$name: $secs%.3f seconds") }
    logWriter.close()
  }
}
